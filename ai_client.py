"""Unified AI client: routes to YepAPI (OpenAI SDK) or Anthropic SDK."""
from typing import Any, Dict, Optional


def call_ai(
    prompt: str,
    yep_api_key: Optional[str] = None,
    anthropic_api_key: Optional[str] = None,
    max_tokens: int = 2000,
) -> Dict[str, Any]:
    """Call AI with whichever key is provided. YepAPI takes precedence."""
    if yep_api_key:
        try:
            import openai
            client = openai.OpenAI(
                base_url="https://api.yepapi.com/v1/ai",
                api_key=yep_api_key,
            )
            response = client.chat.completions.create(
                model="anthropic/claude-haiku-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            return {"text": response.choices[0].message.content, "provider": "yepapi"}
        except Exception as e:
            return {"error": f"YepAPI error: {e}"}

    if anthropic_api_key:
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=anthropic_api_key)
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return {"text": message.content[0].text, "provider": "anthropic"}
        except Exception as e:
            return {"error": f"Anthropic error: {e}"}

    return {"error": "No API key provided. Add a YepAPI or Anthropic key in the sidebar."}


def has_any_key(yep_key: Optional[str], ant_key: Optional[str]) -> bool:
    return bool((yep_key and yep_key.strip()) or (ant_key and ant_key.strip()))
