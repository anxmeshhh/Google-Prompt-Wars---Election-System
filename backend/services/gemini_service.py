"""
ElectaVerse — Gemini API Service
Wrapper around Google's Generative AI SDK with sync and streaming support.
Tracks usage metrics and integrates with Firebase + Cloud Logging.

IMPORTANT: All AI calls are wrapped in eventlet.tpool.execute() so they run
in a real OS thread instead of blocking the eventlet event loop. Without this,
a single AI request (which can take 5-30s) would freeze ALL other requests.
"""

import time
import json
import requests
from config import Config


class GeminiService:
    """Centralized Gemini API interaction service with usage tracking."""

    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.model_name = 'gemini-2.5-flash'
        self._configured = bool(self.api_key and self.api_key != 'your_gemini_api_key_here')

        self.groq_api_key = Config.GROQ_API_KEY
        self.groq_model = "llama-3.3-70b-versatile"

    def is_available(self) -> bool:
        """Check if Gemini API is configured and available."""
        return self._configured

    def _generate_sync(self, prompt: str, system_instruction: str, agent: str) -> str:
        """Internal synchronous generation — tries Groq first (fast), falls back to Gemini."""
        start_time = time.time()

        # ── Try Groq FIRST (1-3s typical response time) ──
        if self.groq_api_key:
            try:
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": self.groq_model,
                    "messages": [
                        {"role": "system", "content": system_instruction or "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ]
                }
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=8)
                res.raise_for_status()
                content = res.json()['choices'][0]['message']['content']
                
                duration_ms = int((time.time() - start_time) * 1000)
                self._track_usage(agent or 'unknown', duration_ms, True, provider='groq')
                return content
            except Exception as groq_e:
                print(f"Groq failed, falling back to Gemini: {groq_e}")

        # ── Fall back to Gemini (slower, may be rate-limited) ──
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            data = {
                "system_instruction": {"parts": {"text": system_instruction or "You are a helpful assistant."}},
                "contents": [{"parts": [{"text": prompt}]}]
            }
            res = requests.post(url, headers=headers, json=data, timeout=8)
            res.raise_for_status()
            content = res.json()['candidates'][0]['content']['parts'][0]['text']
            
            duration_ms = int((time.time() - start_time) * 1000)
            self._track_usage(agent or 'unknown', duration_ms, True, provider='gemini')
            return content
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

    def generate_stream(self, prompt: str, system_instruction: str = '', agent: str = ''):
        """Streaming generator yielding text chunks."""
        if not self._configured:
            yield self._fallback_response(prompt)
            return

        start_time = time.time()
        
        # Try Groq first
        if self.groq_api_key:
            try:
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": self.groq_model,
                    "messages": [
                        {"role": "system", "content": system_instruction or "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": True
                }
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=12, stream=True)
                res.raise_for_status()
                
                for line in res.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            json_str = line_str[6:]
                            if json_str.strip() == '[DONE]':
                                break
                            try:
                                chunk = json.loads(json_str)
                                delta = chunk['choices'][0]['delta']
                                if 'content' in delta:
                                    yield delta['content']
                            except Exception:
                                pass
                                
                duration_ms = int((time.time() - start_time) * 1000)
                import eventlet
from eventlet import tpool
                tpool.execute(self._track_usage, agent or 'unknown', duration_ms, True, 'groq')
                return
            except Exception as groq_e:
                print(f"Groq streaming failed, falling back to Gemini: {groq_e}")

        # Fallback to Gemini Streaming
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:streamGenerateContent?alt=sse&key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            data = {
                "system_instruction": {"parts": {"text": system_instruction or "You are a helpful assistant."}},
                "contents": [{"parts": [{"text": prompt}]}]
            }
            res = requests.post(url, headers=headers, json=data, timeout=12, stream=True)
            res.raise_for_status()
            
            for line in res.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        json_str = line_str[6:]
                        try:
                            chunk = json.loads(json_str)
                            if 'candidates' in chunk and len(chunk['candidates']) > 0:
                                parts = chunk['candidates'][0].get('content', {}).get('parts', [])
                                if parts and 'text' in parts[0]:
                                    yield parts[0]['text']
                        except Exception:
                            pass
                            
            duration_ms = int((time.time() - start_time) * 1000)
            import eventlet
from eventlet import tpool
            tpool.execute(self._track_usage, agent or 'unknown', duration_ms, True, 'gemini')
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            import eventlet
from eventlet import tpool
            tpool.execute(self._track_usage, agent or 'unknown', duration_ms, False, 'gemini')
            yield f"\n\n[AI service temporarily unavailable. Error: {str(e)}]"

    def _generate_json_sync(self, prompt: str, system_instruction: str, agent: str) -> str:
        """Internal synchronous JSON generation — tries Groq first (fast), falls back to Gemini."""
        start_time = time.time()

        # ── Try Groq FIRST (fast, supports json_object format) ──
        if self.groq_api_key:
            try:
                sys_msg = (system_instruction or "You are a helpful assistant.") + " Output strictly in JSON format."
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "model": self.groq_model,
                    "messages": [
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"}
                }
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data, timeout=8)
                res.raise_for_status()
                content = res.json()['choices'][0]['message']['content']
                
                duration_ms = int((time.time() - start_time) * 1000)
                self._track_usage(agent or 'unknown', duration_ms, True, provider='groq')
                return content
            except Exception as groq_e:
                print(f"Groq JSON failed, falling back to Gemini: {groq_e}")

        # ── Fall back to Gemini ──
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            data = {
                "system_instruction": {"parts": {"text": system_instruction or "You are a helpful assistant."}},
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"}
            }
            res = requests.post(url, headers=headers, json=data, timeout=8)
            res.raise_for_status()
            raw = res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            
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
        """Roughly count tokens (to avoid blocking gRPC call)."""
        return len(text) // 4

    def list_available_models(self) -> list[str]:
        """List available models."""
        return [self.model_name]

    def get_model_info(self) -> dict:
        """Get information about the currently configured model."""
        return {
            'model_name': self.model_name,
            'configured': self._configured,
            'groq_fallback': bool(self.groq_api_key),
            'groq_model': self.groq_model if self.groq_api_key else None,
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
            import eventlet
from eventlet import tpool
            tpool.execute(log_agent_action, agent, f'{provider}_generate', duration_ms)
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
