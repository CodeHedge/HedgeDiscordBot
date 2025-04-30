#discord bot that monitors messages in a list of channels

import discord
from discord.ext import commands
import asyncio
import logging
import os
import json
import re
import datetime
import random
import time
import requests


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Load configuration from JSON file
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

# Load the configuration
config = load_config()
TOKEN = config['token']
CHANNELS = config['channels']
EXCLUDED_USERS = config.get('excluded_users', [])

# Initialize Discord bot with all necessary intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info("Bot is ready and connected to Discord!")

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Check if the message is from a monitored channel
    if str(message.channel.id) in CHANNELS:
        logger.info(f"Message received in monitored channel {message.channel.name}: {message.content}")

        # Example: React to the message
        await message.add_reaction("👀")

        # Example: Reply to the message
        if "hello" in message.content.lower():
            await message.channel.send(f"Hello, {message.author.mention}!")

        # Example: Create and send an embed
        if "info" in message.content.lower():
            embed = discord.Embed(
                title="Bot Information",
                description="This is a sample embed message.",
                color=discord.Color.blue()
            )
            embed.add_field(name="Author", value=message.author.name, inline=False)
            embed.add_field(name="Channel", value=message.channel.name, inline=False)
            embed.set_footer(text="HedgeDiscordBot")
            await message.channel.send(embed=embed)

    # Process commands if any
    await bot.process_commands(message)

@bot.command()
async def ping(ctx):
    """A simple ping command."""
    await ctx.send("Pong! 🏓")

# Run the bot
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid token provided. Please check your configuration.")


