import json
import time
from pathlib import Path

from litellm.integrations.custom_logger import CustomLogger

LEDGER = Path("/ledger/usage.jsonl")


class Ledger(CustomLogger):
    def _write(self, kwargs, status: str) -> None:
        log = kwargs.get("standard_logging_object") or {}
        row = {
            "ts": time.time(),
            "status": status,
            "group": log.get("model_group") or kwargs.get("model"),
            "model": log.get("model"),
            "tokens_in": log.get("prompt_tokens") or 0,
            "tokens_out": log.get("completion_tokens") or 0,
            "latency_s": round(log.get("response_time") or 0, 2),
            "error": (log.get("error_str") or "")[:200] or None,
        }
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with LEDGER.open("a") as f:
            f.write(json.dumps(row) + "\n")

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        self._write(kwargs, "ok")

    async def async_log_failure_event(self, kwargs, response_obj, start_time, end_time):
        self._write(kwargs, "error")


ledger = Ledger()
