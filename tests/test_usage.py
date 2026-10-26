import json
import time

from typer.testing import CliRunner

from tickmark import cli


def test_usage_counts_today_and_flags_spent_budget(tmp_path, monkeypatch):
    ledger = tmp_path / "usage.jsonl"
    now, old = time.time(), time.time() - 3 * 86400
    rows = [
        {"ts": now, "status": "ok", "group": "cloud-lite", "tokens_in": 10, "tokens_out": 5},
        {"ts": now, "status": "error", "group": "cloud-lite", "tokens_in": 0, "tokens_out": 0},
        {"ts": old, "status": "ok", "group": "cloud-lite", "tokens_in": 99, "tokens_out": 99},
        {"ts": now, "status": "ok", "group": "local-main", "tokens_in": 7, "tokens_out": 3},
    ]
    ledger.write_text("\n".join(json.dumps(r) for r in rows))
    monkeypatch.setattr(cli.settings, "ledger_path", ledger)
    monkeypatch.setattr(cli.settings, "daily_budget", {"cloud-lite": 2})

    result = CliRunner().invoke(cli.app, ["usage"], env={"COLUMNS": "200"})

    assert result.exit_code == 0
    cells = [[c.strip() for c in line.split("│")[1:8]] for line in result.output.splitlines()]
    by_group = {row[0]: row[1:] for row in cells if len(row) == 7}
    assert by_group["cloud-lite"] == ["1", "1", "10", "5", "2", "0"]
    assert by_group["local-main"] == ["1", "0", "7", "3", "—", "—"]
