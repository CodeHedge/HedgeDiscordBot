#discord bot that monitors messages in a list of channels

import discord
from discord.ext import commands
import logging
from config import load_config
from commands import registry
from events import EventHandler

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

bot = commands.Bot(command_prefix="!", intents=intents)

# Add the event handler
bot.add_cog(EventHandler(bot))

# Setup all registered commands
registry.setup_commands(bot)

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


