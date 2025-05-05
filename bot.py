#discord bot that monitors messages in a list of channels

import discord
from discord.ext import commands
import logging
from config import load_config
from commands import setup_commands
from events import EventHandler
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Load the configuration
config = load_config()
TOKEN = config['token']

# Initialize Discord bot with all necessary intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

class HedgeBot(commands.Bot):
    async def setup_hook(self):
        """Setup hook to initialize cogs and commands"""
        # Add the event handler
        await self.add_cog(EventHandler(self))
        logger.info("Added EventHandler cog")
        
        # Setup all commands
        setup_commands(self)
        logger.info("Setup all commands")

bot = HedgeBot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    logger.info("Bot is ready and connected to Discord!")

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Check if the message is from a monitored channel (only for non-DM messages)
    if message.guild and str(message.channel.id) in config['channels']:
        logger.info(f"Message received in monitored channel {message.channel.name}: {message.content}")

        # Run the message through the moderation API
        await moderate_message(message.content, str(message.author))

        # Example: Reply to the message
        if "hello bot" in message.content.lower():
            await message.channel.send(f"Hello, {message.author.mention}!")

    # Process commands regardless of the channel type (guild or DM)
    await bot.process_commands(message)

# Run the bot
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid token provided. Please check your configuration.")


