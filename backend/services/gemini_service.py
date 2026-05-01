"""
ElectaVerse — Gemini API Service
Wrapper around Google's Generative AI SDK with sync and streaming support.
"""

import google.generativeai as genai
from config import Config


class GeminiService:
    """Centralized Gemini API interaction service."""

    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.model_name = 'gemini-2.0-flash'
        self._configured = False
        self._configure()

    def _configure(self):
        """Configure the Gemini SDK."""
        if self.api_key and self.api_key != 'your_gemini_api_key_here':
            genai.configure(api_key=self.api_key)
            self._configured = True

    def is_available(self) -> bool:
        """Check if Gemini API is configured and available."""
        return self._configured

    def generate(self, prompt: str, system_instruction: str = '') -> str:
        """
        Synchronous generation. Returns the full text response.
        Falls back to a placeholder if API is not configured.
        """
        if not self._configured:
            return self._fallback_response(prompt)

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction or None,
            )
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"AI service temporarily unavailable. Error: {str(e)}"

    def generate_json(self, prompt: str, system_instruction: str = '') -> str:
        """Generate with JSON output mode."""
        if not self._configured:
            return '{"error": "AI not configured"}'

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction or None,
                generation_config={"response_mime_type": "application/json"},
            )
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f'{{"error": "{str(e)}"}}'

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
