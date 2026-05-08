"""Unified AI client: routes to Gemini (FREE), YepAPI, Anthropic, or OpenAI."""
from typing import Any, Dict, Optional


def call_ai(prompt, yep_api_key=None, anthropic_api_key=None, max_tokens=2000):
    """Auto-detect provider based on key prefix."""
    yep_key = (yep_api_key or "").strip() or None
    other_key = (anthropic_api_key or "").strip() or None
    
    # Gemini (FREE - recommended)
    if other_key and other_key.startswith("AIza"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=other_key)
            
            # Try models in order of preference
            models_to_try = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
            last_error = None
            for model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    if response and hasattr(response, 'text') and response.text:
                        return {"text": response.text, "provider": f"🎯 Google Gemini ({model_name})"}
                    else:
                        last_error = "Empty response from Gemini"
                except Exception as e:
                    last_error = e
                    continue
            return {"error": f"All Gemini models failed: {last_error}"}
        except Exception as e:
            return {"error": f"Gemini error: {str(e)}"}
    
    # YepAPI
    if yep_key or (other_key and other_key.startswith("yep_")):
        key = yep_key or other_key
        try:
            from openai import OpenAI
            client = OpenAI(
                base_url="https://api.yepapi.com/v1/ai",
                api_key=key,
                default_headers={"x-api-key": key},
            )
            response = client.chat.completions.create(
                model="anthropic/claude-haiku-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            return {"text": response.choices[0].message.content, "provider": "YepAPI (Claude Haiku)"}
        except Exception as e:
            return {"error": f"YepAPI error: {str(e)}"}
    
    # Anthropic
    if other_key and other_key.startswith("sk-ant"):
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=other_key)
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return {"text": message.content[0].text, "provider": "Anthropic Claude"}
        except Exception as e:
            return {"error": f"Anthropic error: {str(e)}"}
    
    # OpenAI
    if other_key and other_key.startswith("sk-"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=other_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            return {"text": response.choices[0].message.content, "provider": "OpenAI GPT-4o-mini"}
        except Exception as e:
            return {"error": f"OpenAI error: {str(e)}"}
    
    return {"error": "No valid API key. Get FREE Gemini key at aistudio.google.com/apikey"}


def has_any_key(yep_key=None, ant_key=None):
    return bool((yep_key and yep_key.strip()) or (ant_key and ant_key.strip()))


def detect_provider(key):
    k = (key or "").strip()
    if not k:
        return "None"
    if k.startswith("AIza"):
        return "🎯 Google Gemini (FREE)"
    if k.startswith("yep_"):
        return "YepAPI"
    if k.startswith("sk-ant"):
        return "Anthropic"
    if k.startswith("sk-"):
        return "OpenAI"
    return "Unknown"
