import json
import sys
import time
from collections import defaultdict
from datetime import date, datetime

import openai
import typer
from rich.console import Console
from rich.table import Table

from . import __doc__ as about
from . import gateway
from .config import settings

app = typer.Typer(help=about, no_args_is_help=True)
console = Console()


@app.callback()
def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


@app.command()
def chat(prompt: str, model: str = typer.Option("local-main", help="Model group")) -> None:
    """Stream one answer from a model group through the gateway."""
    start = time.perf_counter()
    first = None
    tokens_out = 0
    try:
        raw = gateway.complete_raw(
            model,
            [{"role": "user", "content": prompt}],
            stream=True,
            stream_options={"include_usage": True},
        )
        served_by = raw.headers.get("x-litellm-model-name", model)
        fallbacks = int(raw.headers.get("x-litellm-attempted-fallbacks", 0))
        cached = "x-litellm-cache-key" in raw.headers
        for chunk in raw.parse():
            if chunk.usage:
                tokens_out = chunk.usage.completion_tokens
            if chunk.choices and chunk.choices[0].delta.content:
                first = first or time.perf_counter()
                sys.stdout.write(chunk.choices[0].delta.content)
                sys.stdout.flush()
    except PermissionError as e:
        console.print(f"[red]refused:[/red] {e}")
        raise typer.Exit(2) from e
    except openai.APIError as e:
        console.print(f"[red]gateway error:[/red] {e.__class__.__name__}: {e.message}")
        raise typer.Exit(1) from e
    total = time.perf_counter() - start
    ttft = (first or time.perf_counter()) - start
    rate = tokens_out / (total - ttft) if total > ttft and tokens_out else 0
    notes = [f"{fallbacks} fallback(s)"] if fallbacks else []
    notes += ["cached"] if cached else []
    console.print(
        f"\n[dim]{model} → {served_by}{''.join(f' · {n}' for n in notes)} · "
        f"first token {ttft:.2f}s · {tokens_out} tokens · {rate:.1f} tok/s[/dim]"
    )


@app.command()
def usage(day: str = typer.Option("today", help="today or YYYY-MM-DD")) -> None:
    """Requests per model group for one day, against the daily free-tier budget."""
    wanted = date.today() if day == "today" else date.fromisoformat(day)
    rows = defaultdict(lambda: {"ok": 0, "error": 0, "in": 0, "out": 0})
    if settings.ledger_path.exists():
        for line in settings.ledger_path.read_text().splitlines():
            r = json.loads(line)
            if datetime.fromtimestamp(r["ts"]).date() != wanted:
                continue
            g = rows[r["group"] or "?"]
            g[r["status"]] += 1
            g["in"] += r["tokens_in"]
            g["out"] += r["tokens_out"]
    table = Table(title=f"Gateway usage {wanted}")
    for col in ("group", "ok", "errors", "tokens in", "tokens out", "budget", "left"):
        table.add_column(col, justify="left" if col == "group" else "right")
    for group in sorted(rows.keys() | settings.daily_budget.keys()):
        g = rows[group]
        budget = settings.daily_budget.get(group)
        used = g["ok"] + g["error"]
        left = "—" if budget is None else str(budget - used)
        style = "red" if budget is not None and used >= budget else None
        table.add_row(
            group,
            str(g["ok"]),
            str(g["error"]),
            str(g["in"]),
            str(g["out"]),
            "—" if budget is None else str(budget),
            left,
            style=style,
        )
    console.print(table)
