import os
import json
import logging
from helper import initialize_offense_files
from member_manager import MemberManager

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
            "sudo": [292142885791465482],
            "analyze_command": {
                "max_days": 365,
                "max_messages": 500
            }
        }
        
        # Write the config to the file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        logger.info(f"Configuration file '{config_path}' created successfully.")
    else:
        # Load the existing config file
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        # Ensure analyze_command configuration exists
        if "analyze_command" not in config:
            config["analyze_command"] = {
                "max_days": 365,
                "max_messages": 500
            }
            # Save the updated config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info("Added analyze command configuration to config.json")

    return config

def get_analyze_limits():
    """Get the limits for the analyze command"""
    config = load_config()
    analyze_config = config.get("analyze_command", {})
    
    # Default values if not found
    max_days = analyze_config.get("max_days", 365)
    max_messages = analyze_config.get("max_messages", 500)
    
    return max_days, max_messages

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
        # Reload the config to ensure fresh data
        return load_config()
    else:
        logger.info(f"Channel {channel_id} is already in the configuration.")
        return config

def remove_channel(channel_id):
    config = load_config()
    if channel_id in config['channels']:
        config['channels'].remove(channel_id)
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        logger.info(f"Channel {channel_id} removed from the configuration.")
        # Reload the config to ensure fresh data
        return load_config()
    else:
        logger.info(f"Channel {channel_id} is not in the configuration.")
        return config

# Initialize member manager
member_manager = MemberManager()