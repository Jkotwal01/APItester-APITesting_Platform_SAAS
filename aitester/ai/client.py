import json
import logging
import os
from typing import Any

import google.generativeai as genai
from google.api_core.exceptions import InvalidArgument, ResourceExhausted

from aitester.core.exceptions import AIEngineError, AIRateLimitError

logger = logging.getLogger("aitester.ai")


class GeminiClient:
    """Client for interacting with Google's Gemini API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            # We don't raise immediately because tests might mock this
            logger.warning("GEMINI_API_KEY is not set. AI operations will fail.")
        else:
            genai.configure(api_key=self.api_key)
            # Use gemini-1.5-pro for complex logic as per project goals
            self.model = genai.GenerativeModel("gemini-1.5-pro")

    async def generate_test_payload(self, prompt: str) -> dict[str, Any]:
        """
        Sends a prompt to Gemini asking for a JSON array of test case payloads.
        """
        if not self.api_key:
            raise AIEngineError("GEMINI_API_KEY is missing. Cannot call AI model.")

        try:
            # Use JSON mode if supported, or just prompt for JSON
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.GenerationConfig(response_mime_type="application/json"),
            )

            content = response.text
            if not content:
                raise AIEngineError("AI returned an empty response.")

            # Parse the JSON response
            result: dict[str, Any] = json.loads(content)
            return result

        except ResourceExhausted as e:
            logger.error("Gemini API rate limit exceeded.")
            raise AIRateLimitError("Gemini API rate limit exceeded.") from e
        except InvalidArgument as e:
            logger.error(f"Invalid argument to Gemini API: {e}")
            raise AIEngineError(f"Invalid API argument: {e}") from e
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            raise AIEngineError("AI response was not valid JSON.") from e
        except Exception as e:
            logger.error(f"Unexpected AI error: {e}")
            raise AIEngineError(f"Unexpected AI engine error: {e}") from e

    async def generate_with_retry(self, prompt: str, validator: Any, max_retries: int = 3) -> Any:
        """
        Sends a prompt to Gemini and validates the output with the provided validator.
        Retries up to max_retries times if the validation fails.
        """
        from aitester.core.exceptions import AIOutputValidationError

        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                # Use JSON mode if supported, or just prompt for JSON
                response = await self.model.generate_content_async(
                    prompt,
                    generation_config=genai.GenerationConfig(response_mime_type="application/json"),
                )

                content = response.text
                if not content:
                    raise AIOutputValidationError("AI returned an empty response.")

                validated: Any = validator(content)
                return validated

            except ResourceExhausted as e:
                logger.error("Gemini API rate limit exceeded.")
                raise AIRateLimitError("Gemini API rate limit exceeded.") from e
            except InvalidArgument as e:
                logger.error(f"Invalid argument to Gemini API: {e}")
                raise AIEngineError(f"Invalid API argument: {e}") from e
            except AIOutputValidationError as e:
                last_error = e
                logger.warning(f"AI output validation failed on attempt {attempt + 1}: {e}")
                # We could append the error to the prompt for the next attempt, but simple retry is fine for MVP
            except Exception as e:
                last_error = e
                logger.warning(f"Unexpected AI error on attempt {attempt + 1}: {e}")

        raise last_error or AIEngineError("Failed to generate valid AI output after max retries.")
