import os
import json
import logging
from helper import initialize_offense_files

logger = logging.getLogger(__name__)

def load_config():
    config_path = 'config.json'
    if not os.path.exists(config_path):
        logger.warning(f"Configuration file '{config_path}' not found. Creating a new one.")
        
        # Prompt the user for the token and first channel ID
        token = input("Enter your Discord bot token: ").strip()
        first_channel_id = input("Enter the first channel ID to monitor: ").strip()
        openai_api_key = input("Enter your OpenAI API key (or leave blank): ").strip()

        # Create the config dictionary
        config = {
            "token": token,
            "channels": [first_channel_id],
            "excluded_users": [],
            "openai_api_key": openai_api_key,
            "openai_model": "gpt-3.5-turbo",
            "sudo" : [292142885791465482]  
        }
        
        # Write the config to the file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        logger.info(f"Configuration file '{config_path}' created successfully.")
    else:
        # Load the existing config file
        with open(config_path, 'r') as f:
            config = json.load(f)

    return config

def load_moderation():
    """Initialize all moderation files"""
    # Use the helper function to initialize all needed files
    initialize_offense_files()
    logger.info("Moderation files initialized successfully.")
    
def add_channel(channel_id):
    config = load_config()
    if channel_id not in config['channels']:
        config['channels'].append(channel_id)
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        logger.info(f"Channel {channel_id} added to the configuration.")
    else:
        logger.info(f"Channel {channel_id} is already in the configuration.")