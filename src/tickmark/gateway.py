from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from openai import OpenAI

from .config import settings

LOCAL_GROUPS = frozenset({"local-main", "local-vision", "local-embed"})


def _allowed(group: str) -> str:
    if settings.local_only and group not in LOCAL_GROUPS:
        raise PermissionError(f"{group} is not a local model and this workspace is local-only")
    return group


client = OpenAI(base_url=settings.gateway_url, api_key=settings.gateway_key, max_retries=0)


def complete(group: str, messages: list[dict], **kw):
    return client.chat.completions.create(model=_allowed(group), messages=messages, **kw)


def complete_raw(group: str, messages: list[dict], **kw):
    return client.chat.completions.with_raw_response.create(
        model=_allowed(group), messages=messages, **kw
    )


def chat_model(group: str, **kw) -> ChatOpenAI:
    kw.setdefault("max_retries", 0)
    return ChatOpenAI(
        model=_allowed(group), base_url=settings.gateway_url, api_key=settings.gateway_key, **kw
    )


def embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=_allowed("local-embed"),
        base_url=settings.gateway_url,
        api_key=settings.gateway_key,
        check_embedding_ctx_length=False,
    )
