from tickmark.config import Settings


def test_local_only_reads_env(monkeypatch):
    monkeypatch.setenv("TICKMARK_LOCAL_ONLY", "1")
    assert Settings(_env_file=None).local_only is True


def test_daily_budget_parses_json(monkeypatch):
    monkeypatch.setenv("TICKMARK_DAILY_BUDGET", '{"cloud-lite": 7}')
    assert Settings(_env_file=None).daily_budget == {"cloud-lite": 7}
