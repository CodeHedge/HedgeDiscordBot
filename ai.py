import openai
import asyncio
from config import load_config  # Reuse the load_config function

async def process_ai_request(prompt: str) -> str:
    # Load config and retrieve the OpenAI API key.
    config = load_config()
    openai_key = config.get("openai_api_key")
    openai_model = config.get("openai_model")
    if not openai_key:
        return "OpenAI API key is not configured."

    # Initialize OpenAI client.
    client = openai.OpenAI(api_key=openai_key)

    try:
        # Run the API call in a background thread to avoid blocking.
        response = await asyncio.to_thread(
            lambda: client.responses.create(
                model=openai_model,
                instructions="You are an AI assistant.",
                input=prompt,
            )
        )
        answer = response.output_text.strip()
        return answer
    except Exception as e:
        return "Sorry, something went wrong processing your request."