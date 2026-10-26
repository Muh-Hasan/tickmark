import pytest

from tickmark import gateway


@pytest.fixture
def local_only(monkeypatch):
    monkeypatch.setattr(gateway.settings, "local_only", True)


@pytest.mark.parametrize("group", ["cloud-lite", "cloud-strong", "cloud-backup", "chaos", "typo"])
def test_local_only_refuses_non_local_groups(local_only, group):
    with pytest.raises(PermissionError):
        gateway.complete(group, [{"role": "user", "content": "hi"}])
    with pytest.raises(PermissionError):
        gateway.complete_raw(group, [{"role": "user", "content": "hi"}])
    with pytest.raises(PermissionError):
        gateway.chat_model(group)


def test_local_only_allows_local_groups(local_only):
    assert gateway.chat_model("local-main").model_name == "local-main"
    assert gateway.embeddings().model == "local-embed"


def test_cloud_allowed_when_not_local_only(monkeypatch):
    monkeypatch.setattr(gateway.settings, "local_only", False)
    assert gateway.chat_model("cloud-lite").model_name == "cloud-lite"
