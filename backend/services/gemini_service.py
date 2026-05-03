"""
ElectaVerse — Gemini API Service
Wrapper around Google's Generative AI SDK with sync and streaming support.
Tracks usage metrics and integrates with Firebase + Cloud Logging.

IMPORTANT: All AI calls are wrapped in eventlet.tpool.execute() so they run
in a real OS thread instead of blocking the eventlet event loop. Without this,
a single AI request (which can take 5-30s) would freeze ALL other requests.
"""

import time
import google.generativeai as genai
from config import Config
from groq import Groq


def _run_in_thread(fn, *args, **kwargs):
    """
    DEPRECATED: We no longer offload to native threads.
    Eventlet monkey patching automatically makes httpx and requests non-blocking.
    Using native threads (tpool) causes deadlocks with monkey-patched threading locks.
    """
    return fn(*args, **kwargs)


class GeminiService:
    """Centralized Gemini API interaction service with usage tracking."""

    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.model_name = 'gemini-2.5-flash'
        self._configured = False
        self._configure()

        self.groq_api_key = Config.GROQ_API_KEY
        self.groq_client = Groq(api_key=self.groq_api_key) if self.groq_api_key else None
        self.groq_model = "llama-3.3-70b-versatile"

    def _configure(self):
        """Configure the Gemini SDK."""
        if self.api_key and self.api_key != 'your_gemini_api_key_here':
            genai.configure(api_key=self.api_key)
            self._configured = True

    def is_available(self) -> bool:
        """Check if Gemini API is configured and available."""
        return self._configured

    def _generate_sync(self, prompt: str, system_instruction: str, agent: str) -> str:
        """Internal synchronous generation — tries Groq first (fast), falls back to Gemini."""
        start_time = time.time()

        # ── Try Groq FIRST (1-3s typical response time) ──
        if self.groq_client:
            try:
                completion = self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[
                        {"role": "system", "content": system_instruction or "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
                duration_ms = int((time.time() - start_time) * 1000)
                self._track_usage(agent or 'unknown', duration_ms, True, provider='groq')
                return completion.choices[0].message.content
            except Exception as groq_e:
                print(f"Groq failed, falling back to Gemini: {groq_e}")

        # ── Fall back to Gemini (slower, may be rate-limited) ──
        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction or None,
            )
            response = model.generate_content(
                prompt,
                request_options={'timeout': 8},
            )
            duration_ms = int((time.time() - start_time) * 1000)
            self._track_usage(agent or 'unknown', duration_ms, True, provider='gemini')
            return response.text
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self._track_usage(agent or 'unknown', duration_ms, False)
            return f"AI service temporarily unavailable. Error: {str(e)}"

    def generate(self, prompt: str, system_instruction: str = '', agent: str = '') -> str:
        """
        Generation using eventlet. Network sockets are natively non-blocking
        due to eventlet.monkey_patch().
        """
        if not self._configured:
            return self._fallback_response(prompt)
        return self._generate_sync(prompt, system_instruction, agent)

    def _generate_json_sync(self, prompt: str, system_instruction: str, agent: str) -> str:
        """Internal synchronous JSON generation — tries Groq first (fast), falls back to Gemini."""
        import json
        start_time = time.time()

        # ── Try Groq FIRST (fast, supports json_object format) ──
        if self.groq_client:
            try:
                sys_msg = (system_instruction or "You are a helpful assistant.") + " Output strictly in JSON format."
                completion = self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                duration_ms = int((time.time() - start_time) * 1000)
                self._track_usage(agent or 'unknown', duration_ms, True, provider='groq')
                return completion.choices[0].message.content
            except Exception as groq_e:
                print(f"Groq JSON failed, falling back to Gemini: {groq_e}")

        # ── Fall back to Gemini ──
        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction or None,
                generation_config={"response_mime_type": "application/json"},
            )
            response = model.generate_content(
                prompt,
                request_options={'timeout': 8},
            )
            raw = response.text.strip()
            # Strip markdown code fences if present
            if raw.startswith('```'):
                lines = raw.split('\n')
                if len(lines) > 1:
                    raw = '\n'.join(lines[1:])
                if raw.endswith('```'):
                    raw = raw[:-3].strip()
            duration_ms = int((time.time() - start_time) * 1000)
            self._track_usage(agent or 'unknown', duration_ms, True, provider='gemini')
            return raw
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self._track_usage(agent or 'unknown', duration_ms, False)
            return json.dumps({"error": str(e)})

    def generate_json(self, prompt: str, system_instruction: str = '', agent: str = '') -> str:
        """Generation using eventlet non-blocking sockets."""
        if not self._configured:
            return '{"error": "AI not configured"}'
        return self._generate_json_sync(prompt, system_instruction, agent)

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string using Gemini's tokenizer."""
        if not self._configured:
            # Rough estimate: ~4 chars per token
            return len(text) // 4
        try:
            model = genai.GenerativeModel(model_name=self.model_name)
            result = model.count_tokens(text)
            return result.total_tokens
        except Exception:
            return len(text) // 4

    def list_available_models(self) -> list[str]:
        """List all available Gemini models."""
        if not self._configured:
            return []
        try:
            models = genai.list_models()
            return [
                m.name for m in models
                if 'generateContent' in (m.supported_generation_methods or [])
            ]
        except Exception:
            return []

    def get_model_info(self) -> dict:
        """Get information about the currently configured model."""
        return {
            'model_name': self.model_name,
            'configured': self._configured,
            'groq_fallback': self.groq_client is not None,
            'groq_model': self.groq_model if self.groq_client else None,
        }

    def _track_usage(self, agent: str, duration_ms: int, success: bool, provider: str = 'gemini') -> None:
        """Log usage metrics to Firebase and Cloud Logging (fire-and-forget)."""
        try:
            from services.firebase_service import save_agent_metric
            save_agent_metric(agent, duration_ms, provider, success)
        except Exception:
            pass

        try:
            from services.gcloud_logging_service import log_agent_action
            log_agent_action(agent, f'{provider}_generate', duration_ms)
        except Exception:
            pass

    def _fallback_response(self, prompt: str) -> str:
        """Provide a helpful response when API key is not configured."""
        return (
            "🔑 **Gemini API key not configured.**\n\n"
            "To enable AI features, add your API key to the `.env` file:\n"
            "```\nGEMINI_API_KEY=your_key_here\n```\n\n"
            "Get a free key at [Google AI Studio](https://aistudio.google.com/apikey).\n\n"
            "The real-time simulation engine and dashboard work without an API key."
        )


# Singleton instance
gemini = GeminiService()
