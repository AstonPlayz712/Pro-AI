"""Multi-model router supporting multiple AI providers"""

from typing import Optional
import httpx
import json


class ModelRouter:
    """Routes requests to different AI model providers"""

    def __init__(self, config: dict):
        """
        Initialize model router.

        Args:
            config: Configuration dictionary with model settings
        """
        self.config = config

    async def chat(
        self,
        messages: list,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None,
    ) -> dict:
        """
        Send a chat request to the selected model.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model provider name (openai, anthropic, google, ollama)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system-level instruction prepended to every request

        Returns:
            Response dictionary with model output
        """
        if model is None:
            model = self.config.get("default_model", "openai")

        if model == "openai":
            return await self._chat_openai(messages, temperature, max_tokens, system_prompt)
        elif model == "anthropic":
            return await self._chat_anthropic(messages, temperature, max_tokens, system_prompt)
        elif model == "google":
            return await self._chat_google(messages, temperature, max_tokens, system_prompt)
        elif model == "ollama":
            return await self._chat_ollama(messages, temperature, max_tokens, system_prompt)
        else:
            return {"error": f"Unknown model: {model}"}

    async def _chat_openai(
        self,
        messages: list,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str] = None,
    ) -> dict:
        """Chat with OpenAI API"""
        try:
            import openai

            openai.api_key = self.config.get("openai", {}).get("api_key")
            model_name = self.config.get("openai", {}).get("model", "gpt-4")

            messages_with_system = messages
            if system_prompt:
                messages_with_system = [{"role": "system", "content": system_prompt}] + messages

            response = await openai.ChatCompletion.acreate(
                model=model_name,
                messages=messages_with_system,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return {
                "model": "openai",
                "content": response.choices[0].message.content,
                "usage": response.usage.dict(),
            }
        except Exception as e:
            return {"error": f"OpenAI error: {str(e)}"}

    async def _chat_anthropic(
        self,
        messages: list,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str] = None,
    ) -> dict:
        """Chat with Anthropic API"""
        try:
            from anthropic import AsyncAnthropic

            api_key = self.config.get("anthropic", {}).get("api_key")
            model_name = self.config.get("anthropic", {}).get("model", "claude-3-sonnet-20240229")

            client = AsyncAnthropic(api_key=api_key)

            create_kwargs: dict = {
                "model": model_name,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages,
            }
            if system_prompt:
                create_kwargs["system"] = system_prompt

            response = await client.messages.create(**create_kwargs)

            return {
                "model": "anthropic",
                "content": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
            }
        except Exception as e:
            return {"error": f"Anthropic error: {str(e)}"}

    async def _chat_google(
        self,
        messages: list,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str] = None,
    ) -> dict:
        """Chat with Google Gemini API"""
        try:
            import google.generativeai as genai

            api_key = self.config.get("google", {}).get("api_key")
            model_name = self.config.get("google", {}).get("model", "gemini-1.5-pro")

            genai.configure(api_key=api_key)

            model_kwargs: dict = {}
            if system_prompt:
                model_kwargs["system_instruction"] = system_prompt

            model = genai.GenerativeModel(model_name, **model_kwargs)

            response = model.generate_content(
                contents=[msg.get("content", "") for msg in messages],
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )

            return {
                "model": "google",
                "content": response.text,
                "usage": {"total_tokens": 0},  # Google doesn't always provide token count
            }
        except Exception as e:
            return {"error": f"Google error: {str(e)}"}

    async def _chat_ollama(
        self,
        messages: list,
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str] = None,
    ) -> dict:
        """Chat with Ollama local model"""
        try:
            base_url = self.config.get("ollama", {}).get("base_url", "http://localhost:11434")
            model_name = self.config.get("ollama", {}).get("model", "llama2")

            # Convert messages to prompt format; prepend system instruction when present
            parts = []
            if system_prompt:
                parts.append(f"SYSTEM: {system_prompt}")
            parts.extend(f"{msg['role'].upper()}: {msg['content']}" for msg in messages)
            prompt = "\n".join(parts) + "\nASSISTANT:"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "temperature": temperature,
                        "stream": False,
                    },
                )

            result = response.json()

            return {
                "model": "ollama",
                "content": result.get("response", ""),
                "usage": {"tokens": result.get("eval_count", 0)},
            }
        except Exception as e:
            return {"error": f"Ollama error: {str(e)}"}

    def get_available_models(self) -> list:
        """Get list of available model providers"""
        models = []
        if self.config.get("openai", {}).get("api_key"):
            models.append("openai")
        if self.config.get("anthropic", {}).get("api_key"):
            models.append("anthropic")
        if self.config.get("google", {}).get("api_key"):
            models.append("google")
        # Ollama is always available if base_url is set
        if self.config.get("ollama", {}).get("base_url"):
            models.append("ollama")
        return models
