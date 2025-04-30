import os
import json
import logging

logger = logging.getLogger(__name__)

def load_config():
    config_path = 'config.json'
    if not os.path.exists(config_path):
        logger.warning(f"Configuration file '{config_path}' not found. Creating a new one.")
        
        # Prompt the user for the token and first channel ID
        token = input("Enter your Discord bot token: ").strip()
        first_channel_id = input("Enter the first channel ID to monitor: ").strip()
        
        # Create the config dictionary
        config = {
            "token": token,
            "channels": [first_channel_id],
            "excluded_users": []
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