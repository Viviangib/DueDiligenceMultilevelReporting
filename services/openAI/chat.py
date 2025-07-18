from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self, api_key: str = "", model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()
        self.model = model

    async def chat(
        self,
        prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        try:
            params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
            }

            if temperature is not None:
                params["temperature"] = temperature
            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            response = await self.client.chat.completions.create(**params)

            content = response.choices[0].message.content or ""
            return content

        except Exception as e:
            logger.error(f"OpenAI GPT call failed: {e}")
            return f"GPT-4 analysis failed: {e}"
