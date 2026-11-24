import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from backend.core.config import settings

class AIProvider:
    @staticmethod
    def call_gemini(prompt: str) -> Optional[str]:
        api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}]
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return None

    @staticmethod
    def call_openai(prompt: str) -> Optional[str]:
        api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        url = "https://api.openai.com/v1/chat/completions"
        payload = json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        })
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"]
        except Exception:
            return None

    @classmethod
    def generate_completion(cls, prompt: str, system_fallback: callable) -> str:
        """
        Attempts external AI provider if configured, otherwise falls back gracefully
        to deterministic domain-expert healthcare coordination rule engine.
        """
        if settings.AI_PROVIDER == "gemini" or (settings.AI_PROVIDER == "auto" and settings.GEMINI_API_KEY):
            result = cls.call_gemini(prompt)
            if result:
                return result
        elif settings.AI_PROVIDER == "openai" or (settings.AI_PROVIDER == "auto" and settings.OPENAI_API_KEY):
            result = cls.call_openai(prompt)
            if result:
                return result
        
        # Deterministic domain rule engine fallback
        return system_fallback()
