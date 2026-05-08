"""Unified AI client: routes to YepAPI, Anthropic, or OpenAI based on key prefix."""
import os
from typing import Any, Dict, List, Optional

# YepAPI model fallback chain. The first that succeeds is used.
# Override with YEP_MODELS env var (comma-separated).
DEFAULT_YEP_MODELS: List[str] = [
    "anthropic/claude-haiku",
    "anthropic/claude-haiku-4.5",
    "anthropic/claude-sonnet-4",
    "anthropic/claude-sonnet-4.5",
    "openai/gpt-4o-mini",
    "google/gemini-2.5-flash-lite",
    "google/gemini-2.5-flash",
]


def _yep_models() -> List[str]:
    env = os.getenv("YEP_MODELS", "").strip()
    if env:
        return [m.strip() for m in env.split(",") if m.strip()]
    return DEFAULT_YEP_MODELS


def call_ai(
    prompt: str,
    yep_api_key: Optional[str] = None,
    anthropic_api_key: Optional[str] = None,
    max_tokens: int = 2000,
) -> Dict[str, Any]:
    """Auto-detect provider based on key format and route accordingly.

    Returns: {"text": str, "provider": str} on success, {"error": str} on failure.
    """
    yep_key = (yep_api_key or "").strip() or None
    other_key = (anthropic_api_key or "").strip() or None

    # YepAPI: explicit yep_api_key OR a key passed in anthropic_api_key that starts with yep_
    if yep_key or (other_key and other_key.startswith("yep_")):
        key = yep_key or other_key
        try:
            from openai import OpenAI
            client = OpenAI(
                base_url="https://api.yepapi.com/v1/ai",
                api_key=key,
                default_headers={"x-api-key": key},
            )
            last_err: Optional[str] = None
            for model_id in _yep_models():
                try:
                    response = client.chat.completions.create(
                        model=model_id,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens,
                    )
                    return {
                        "text": response.choices[0].message.content,
                        "provider": f"YepAPI ({model_id})",
                    }
                except Exception as model_err:
                    msg = str(model_err)
                    last_err = f"{model_id}: {msg}"
                    # Only retry next model when the failure is model-related
                    is_model_issue = (
                        "is not available" in msg
                        or "model" in msg.lower() and "not" in msg.lower()
                        or "404" in msg
                        or "400" in msg
                    )
                    if not is_model_issue:
                        return {"error": f"YepAPI error: {msg}"}
            return {"error": f"YepAPI: no model in fallback chain succeeded. Last: {last_err}"}
        except Exception as e:
            return {"error": f"YepAPI error: {str(e)}"}

    # Anthropic: sk-ant prefix
    if other_key and other_key.startswith("sk-ant"):
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=other_key)
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return {
                "text": message.content[0].text,
                "provider": "Anthropic (claude-haiku-4-5)",
            }
        except Exception as e:
            return {"error": f"Anthropic error: {str(e)}"}

    # OpenAI: sk- prefix (but not sk-ant, handled above)
    if other_key and other_key.startswith("sk-"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=other_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            return {
                "text": response.choices[0].message.content,
                "provider": "OpenAI (gpt-4o-mini)",
            }
        except Exception as e:
            return {"error": f"OpenAI error: {str(e)}"}

    return {"error": "No valid API key provided"}


def has_any_key(yep_key: Optional[str] = None, ant_key: Optional[str] = None) -> bool:
    """Check if any usable API key is provided."""
    return bool((yep_key and yep_key.strip()) or (ant_key and ant_key.strip()))


def detect_provider(key: str) -> str:
    """Return the provider label for a given key string."""
    k = (key or "").strip()
    if not k:
        return "None"
    if k.startswith("yep_"):
        return "YepAPI"
    if k.startswith("sk-ant"):
        return "Anthropic"
    if k.startswith("sk-"):
        return "OpenAI"
    return "Unknown"
