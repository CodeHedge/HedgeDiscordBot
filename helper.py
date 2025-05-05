import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def initialize_offense_files():
    """Initialize the offense files if they don't exist"""
    # Regular offense counter file
    moderation_path = 'moderation.json'
    if not os.path.exists(moderation_path):
        with open(moderation_path, 'w') as f:
            json.dump({}, f, indent=4)
        logger.info(f"Created moderation file: {moderation_path}")
    
    # Offensive messages storage file
    messages_path = 'offense_messages.json'
    if not os.path.exists(messages_path):
        with open(messages_path, 'w') as f:
            json.dump({}, f, indent=4)
        logger.info(f"Created offense messages file: {messages_path}")

def save_offense(username, category, message_content=None):
    """
    Save an offense and optionally the offensive message
    
    Args:
        username: The username of the offender
        category: The category of the offense
        message_content: The content of the offensive message (optional)
    """
    # Save to offense counter file
    moderation_path = 'moderation.json'
    if not os.path.exists(moderation_path):
        logger.error(f"Moderation file '{moderation_path}' not found.")
        return

    with open(moderation_path, 'r') as f:
        data = json.load(f)

    if username not in data:
        data[username] = {}

    if category not in data[username]:
        data[username][category] = 0

    data[username][category] += 1

    with open(moderation_path, 'w') as f:
        json.dump(data, f, indent=4)

    logger.info(f"Offense recorded: {username} -> {category}")
    
    # Save message content if provided
    if message_content:
        messages_path = 'offense_messages.json'
        if not os.path.exists(messages_path):
            with open(messages_path, 'w') as f:
                json.dump({}, f, indent=4)
            logger.info(f"Created offense messages file: {messages_path}")
            
        with open(messages_path, 'r') as f:
            messages_data = json.load(f)
            
        if username not in messages_data:
            messages_data[username] = []
            
        # Add the new offensive message with timestamp and category
        timestamp = datetime.now().isoformat()
        
        # Truncate very long messages
        if len(message_content) > 500:
            message_content = message_content[:497] + "..."
            
        messages_data[username].append({
            "timestamp": timestamp,
            "category": category,
            "content": message_content
        })
        
        # Keep only the 20 most recent messages per user
        if len(messages_data[username]) > 20:
            messages_data[username] = sorted(messages_data[username], 
                                            key=lambda x: x["timestamp"], 
                                            reverse=True)[:20]
        
        with open(messages_path, 'w') as f:
            json.dump(messages_data, f, indent=4)
            
        logger.info(f"Saved offensive message for user: {username}")

def get_recent_offensive_messages(username, limit=3):
    """
    Get the most recent offensive messages for a user
    
    Args:
        username: The username to get messages for
        limit: Maximum number of messages to return
        
    Returns:
        list: List of recent offensive messages
    """
    messages_path = 'offense_messages.json'
    if not os.path.exists(messages_path):
        logger.warning(f"Offense messages file '{messages_path}' not found.")
        return []
        
    with open(messages_path, 'r') as f:
        messages_data = json.load(f)
    
    # Debug log to see what data we have
    logger.info(f"Messages data keys: {list(messages_data.keys())}")
    logger.info(f"Looking for messages for username: '{username}'")
        
    if username not in messages_data:
        logger.warning(f"No messages found for user: {username}")
        return []
        
    user_messages = messages_data[username]
    logger.info(f"Found {len(user_messages)} messages for user {username}")
    
    # Sort messages by timestamp (newest first) and return up to limit
    sorted_messages = sorted(user_messages, 
                           key=lambda x: x["timestamp"], 
                           reverse=True)[:limit]
                           
    return sorted_messages