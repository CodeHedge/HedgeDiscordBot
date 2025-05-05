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
            lambda: client.chat.completions.create(
                model=openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error in process_ai_request: {e}")
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
                model="text-moderation-latest",
                input=content,
            )
        )

        logger.info(f"Moderation API response for user '{username}': {response}")

        # Handle the moderation response
        if hasattr(response, 'results') and response.results:
            result = response.results[0]
            if hasattr(result, 'flagged') and result.flagged:
                for category_name, flagged in result.categories.__dict__.items():
                    if flagged:
                        # Pass the message content to save_offense
                        save_offense(username, category_name, content)
                        logger.info(f"Flagged category '{category_name}' for user '{username}'")
        else:
            logger.info(f"No flagged content in message from user '{username}'")

        return "Message processed for moderation."
    except Exception as e:
        logger.error(f"Error during moderation for user '{username}': {e}")
        return f"Error during moderation: {e}"