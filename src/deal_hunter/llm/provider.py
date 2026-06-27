from langchain_openai import ChatOpenAI

from deal_hunter.config import Settings


def get_llm(config: Settings) -> ChatOpenAI:
    return ChatOpenAI(
        base_url=config.LLM_BASE_URL,
        model=config.LLM_MODEL,
        api_key=config.LLM_API_KEY,
        temperature=0.2,
    )
