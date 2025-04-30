import openai
import asyncio
from config import load_config  # Reuse the load_config function
from openai import OpenAI
from helper import save_offense
import logging

logger = logging.getLogger(__name__)

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
        logger.error("OpenAI API key is not configured.")
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

        # Log the raw response from the API
        logger.info(f"Moderation API response for user '{username}': {response}")

        # Parse the results
        results = response.get("results", [])
        if results:
            flagged_categories = results[0].get("categories", {})
            for category, flagged in flagged_categories.items():
                if flagged:
                    save_offense(username, category)
                    logger.info(f"Flagged category '{category}' for user '{username}'.")

        return "Message processed for moderation."
    except Exception as e:
        logger.error(f"Error during moderation for user '{username}': {e}")
        return f"Error during moderation: {e}"