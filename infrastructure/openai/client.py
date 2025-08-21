from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self, api_key: str = "", model: str = "gpt-5-mini-2025-08-07"):
        self.client = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()
        self.model = model

    async def chat(
        self,
        prompt: str,
        max_tokens: int | None = None,
    ) -> str:
        try:
            params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
            }


            if max_tokens is not None:
                # Use max_completion_tokens for newer models, fallback to max_tokens for older ones
                if any(model_name in self.model.lower() for model_name in ["gpt-4o", "gpt-4-turbo", "gpt-5", "o1"]):
                    params["max_completion_tokens"] = max_tokens
                else:
                    params["max_tokens"] = max_tokens

            response = await self.client.chat.completions.create(**params)

            content = response.choices[0].message.content or ""
            return content

        except Exception as e:
            logger.error(f"OpenAI GPT call failed: {e}")
            return f"GPT-4 analysis failed: {e}"


