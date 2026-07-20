"""
OpenRouter chat-completions client.

This is the ONLY outbound LLM integration in the project. No OpenAI, Gemini,
Anthropic, Azure, Groq or local model SDK is used anywhere; every generation
request is an HTTPS call to https://openrouter.ai/api/v1/chat/completions.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, Generator, List, Optional

import requests

from config import settings
from utils.logger import get_logger
from utils.text_utils import strip_code_fences, strip_html_breaks

logger = get_logger(__name__)


class OpenRouterError(RuntimeError):
    """Raised when OpenRouter cannot fulfil a request."""


class OpenRouterClient:
    """Thin, retrying wrapper around the OpenRouter chat-completions endpoint."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.api_key: str = api_key or settings.openrouter_api_key
        self.model: str = model or settings.openrouter_model
        self.base_url: str = (base_url or settings.openrouter_base_url).rstrip("/")
        self._session = requests.Session()

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # Optional OpenRouter attribution headers.
            "HTTP-Referer": settings.openrouter_referer,
            "X-Title": settings.openrouter_title,
        }

    def _payload(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float],
        max_tokens: Optional[int],
        stream: bool,
    ) -> Dict[str, Any]:
        return {
            "model": self.model,
            "messages": messages,
            "temperature": settings.temperature if temperature is None else temperature,
            "max_tokens": max_tokens or settings.max_tokens,
            "stream": stream,
        }

    def _guard_key(self) -> None:
        if not self.api_key:
            raise OpenRouterError(
                "No OpenRouter API key found. Add OPENROUTER_API_KEY to your .env "
                "file locally, or to Secrets in Streamlit Cloud."
            )

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Send a blocking chat request and return the assistant's text."""
        self._guard_key()
        url = f"{self.base_url}/chat/completions"
        payload = self._payload(messages, temperature, max_tokens, stream=False)

        last_error: Optional[Exception] = None
        for attempt in range(1, settings.max_retries + 1):
            try:
                response = self._session.post(
                    url,
                    headers=self._headers,
                    json=payload,
                    timeout=settings.request_timeout,
                )
                if response.status_code == 401:
                    raise OpenRouterError("OpenRouter rejected the API key (401).")
                if response.status_code == 402:
                    raise OpenRouterError("OpenRouter account is out of credits (402).")
                if response.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning("Rate limited by OpenRouter, retrying in %ss", wait)
                    time.sleep(wait)
                    continue
                response.raise_for_status()

                data = response.json()
                choices = data.get("choices") or []
                if not choices:
                    raise OpenRouterError(f"Empty response from OpenRouter: {data}")
                content = (choices[0].get("message") or {}).get("content", "").strip()
                return strip_html_breaks(content)

            except OpenRouterError:
                raise
            except requests.RequestException as exc:
                last_error = exc
                logger.warning("OpenRouter attempt %s/%s failed: %s",
                               attempt, settings.max_retries, exc)
                time.sleep(min(2 ** attempt, 8))

        raise OpenRouterError(f"OpenRouter request failed after retries: {last_error}")

    def stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Generator[str, None, None]:
        """
        Stream tokens from OpenRouter.

        Yields incremental text fragments so the UI can render a live typing
        animation via ``st.write_stream``.
        """
        self._guard_key()
        url = f"{self.base_url}/chat/completions"
        payload = self._payload(messages, temperature, max_tokens, stream=True)

        try:
            with self._session.post(
                url,
                headers=self._headers,
                json=payload,
                timeout=settings.request_timeout,
                stream=True,
            ) as response:
                response.raise_for_status()
                for raw_line in response.iter_lines(decode_unicode=True):
                    if not raw_line or not raw_line.startswith("data:"):
                        continue
                    data_str = raw_line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        delta = json.loads(data_str)["choices"][0].get("delta", {})
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
                    token = delta.get("content")
                    if token:
                        yield token
        except requests.RequestException as exc:
            logger.error("Streaming failed, falling back to blocking call: %s", exc)
            yield self.chat(messages, temperature, max_tokens)

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Any:
        """
        Request a JSON payload and parse it.

        Models occasionally wrap JSON in Markdown fences or add a preamble, so
        the response is cleaned and, as a last resort, the outermost JSON
        array/object is extracted by bracket matching.
        """
        raw = self.chat(messages, temperature, max_tokens)
        cleaned = strip_code_fences(raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            for opener, closer in (("[", "]"), ("{", "}")):
                start, end = cleaned.find(opener), cleaned.rfind(closer)
                if start != -1 and end > start:
                    try:
                        return json.loads(cleaned[start : end + 1])
                    except json.JSONDecodeError:
                        continue
            logger.error("Could not parse JSON from model output: %s", raw[:400])
            raise OpenRouterError("The model did not return valid JSON. Please retry.")

    def health_check(self) -> tuple[bool, str]:
        """Verify the key works. Returns ``(ok, message)``."""
        try:
            self.chat([{"role": "user", "content": "Reply with the single word: ok"}],
                      max_tokens=5)
            return True, "Connected to OpenRouter"
        except Exception as exc:  # noqa: BLE001 - surfaced to the UI
            return False, str(exc)
