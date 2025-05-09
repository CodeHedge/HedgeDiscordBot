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
                max_tokens=5000
            )
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Error in process_ai_request: {e}")
        return "Sorry, something went wrong processing your request."

async def moderate_message(content: str, username: str):
    """
    Moderate a message using OpenAI's moderation API and store flagged content.
    
    Args:
        content: The message content to moderate
        username: The username of the message author
    """
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

        # Check if any content was flagged
        if hasattr(response, 'results') and response.results:
            result = response.results[0]
            if hasattr(result, 'flagged') and result.flagged:
                logger.info(f"Content from user '{username}' was flagged")
                
                # Iterate through categories and log flagged ones
                flagged_categories = []
                for category_name, flagged in result.categories.__dict__.items():
                    if flagged:
                        flagged_categories.append(category_name)
                        # Save the offense and the message content
                        save_offense(username, category_name, content)
                        logger.info(f"Flagged category '{category_name}' for user '{username}'")
                
                if flagged_categories:
                    logger.info(f"Message flagged for categories: {flagged_categories}")
                    return "Message flagged for moderation."
            else:
                logger.info(f"Content from user '{username}' was not flagged")
        else:
            logger.info(f"No results in moderation response for user '{username}'")

        return "Message processed for moderation."
    except Exception as e:
        logger.error(f"Error during moderation for user '{username}': {e}")
        return f"Error during moderation: {e}"