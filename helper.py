import json
import os
import logging

logger = logging.getLogger(__name__)

def save_offense(username, category):
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