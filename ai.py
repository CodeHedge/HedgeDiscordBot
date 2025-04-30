import openai
import asyncio
from config import load_config  # Reuse the load_config function
from openai import OpenAI
from helper import save_offense

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

async def moderate_message(content: str, username: str):
    # Load config and retrieve the OpenAI API key.
    config = load_config()
    openai_key = config.get("openai_api_key")
    if not openai_key:
        return "OpenAI API key is not configured."

    client = OpenAI(api_key=openai_key)

    try:
        # Call the moderation API
        response = await asyncio.to_thread(
            lambda: client.moderations.create(
                model="omni-moderation-latest",
                input=content,
            )
        )

        # Parse the results
        results = response.get("results", [])
        if results:
            flagged_categories = results[0].get("categories", {})
            for category, flagged in flagged_categories.items():
                if flagged:
                    save_offense(username, category)

        return "Message processed for moderation."
    except Exception as e:
        return f"Error during moderation: {e}"