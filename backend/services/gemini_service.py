"""
ElectaVerse — Gemini API Service
Wrapper around Google's Generative AI SDK with sync and streaming support.
"""

import google.generativeai as genai
from config import Config
from groq import Groq


class GeminiService:
    """Centralized Gemini API interaction service."""

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
            if self.groq_client:
                print(f"Gemini failed, falling back to Groq: {e}")
                try:
                    completion = self.groq_client.chat.completions.create(
                        model=self.groq_model,
                        messages=[
                            {"role": "system", "content": system_instruction or "You are a helpful assistant."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    return completion.choices[0].message.content
                except Exception as groq_e:
                    return f"AI service temporarily unavailable. Groq Error: {str(groq_e)}"
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
            raw = response.text.strip()
            # Strip markdown code fences if present
            if raw.startswith('```'):
                lines = raw.split('\n')
                if len(lines) > 1:
                    raw = '\n'.join(lines[1:])
                if raw.endswith('```'):
                    raw = raw[:-3].strip()
            return raw
        except Exception as e:
            if self.groq_client:
                print(f"Gemini failed, falling back to Groq JSON: {e}")
                try:
                    # Groq strictly requires the word JSON in the prompt for json_object format.
                    # All our agents already have this, but we append to system_instruction to be perfectly safe.
                    sys_msg = (system_instruction or "You are a helpful assistant.") + " Output strictly in JSON format."
                    completion = self.groq_client.chat.completions.create(
                        model=self.groq_model,
                        messages=[
                            {"role": "system", "content": sys_msg},
                            {"role": "user", "content": prompt}
                        ],
                        response_format={"type": "json_object"}
                    )
                    return completion.choices[0].message.content
                except Exception as groq_e:
                    import json
                    return json.dumps({"error": f"Groq fallback failed: {str(groq_e)}"})

            import json
            return json.dumps({"error": str(e)})

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
