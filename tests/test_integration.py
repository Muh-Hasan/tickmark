import json
import os
import smtplib
import time
import uuid
from email.message import EmailMessage

import httpx
import pytest

from tickmark import gateway
from tickmark.config import settings

pytestmark = pytest.mark.integration

BALANCE_TOOL = {
    "type": "function",
    "function": {
        "name": "get_balance",
        "description": "Current balance of one bank account",
        "parameters": {
            "type": "object",
            "properties": {"account": {"type": "string", "enum": ["operating", "savings", "card"]}},
            "required": ["account"],
        },
    },
}


def ledger_rows_since(ts: float, want: int, timeout: float = 10) -> list[dict]:
    deadline = time.time() + timeout
    while True:
        rows = [json.loads(line) for line in settings.ledger_path.read_text().splitlines()]
        rows = [r for r in rows if r["ts"] >= ts]
        if len(rows) >= want or time.time() > deadline:
            return rows
        time.sleep(0.5)


def test_local_main_makes_a_tool_call():
    reply = gateway.complete(
        "local-main",
        [{"role": "user", "content": "What's the balance of the savings account?"}],
        tools=[BALANCE_TOOL],
        temperature=0,
    )
    call = reply.choices[0].message.tool_calls[0]
    assert call.function.name == "get_balance"
    assert json.loads(call.function.arguments) == {"account": "savings"}


def test_local_embed_returns_768_dims():
    assert len(gateway.embeddings().embed_query("unpaid invoice from Acme")) == 768


def test_429_is_logged_as_error_then_falls_back_to_local_main():
    start = time.time()
    reply = gateway.complete("chaos", [{"role": "user", "content": "Reply with the word ok."}])
    assert reply.choices[0].message.content
    rows = ledger_rows_since(start, want=2)
    assert {(r["group"], r["status"]) for r in rows} >= {("chaos", "error"), ("local-main", "ok")}
    assert all("rate limit" in r["error"] for r in rows if r["group"] == "chaos")


def test_dev_email_lands_in_mailpit():
    subject = f"tickmark smoke {uuid.uuid4().hex[:8]}"
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = "books@tickmark.test", "client@example.test", subject
    msg.set_content("Invoice INV-1042 is due on 2026-11-15.")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.send_message(msg)
    api = f"http://localhost:{os.environ.get('TICKMARK_MAILPIT_UI_PORT', '8026')}/api/v1/search"
    found = httpx.get(api, params={"query": f'subject:"{subject}"'}).json()
    assert found["messages_count"] == 1
