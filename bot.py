#discord bot that monitors messages in a list of channels

import discord
from discord.ext import commands
import asyncio
import logging
from config import load_config  # Import the load_config function
from commands import setup_commands  # Import the setup_commands function

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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

# Load commands
setup_commands(bot)

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

# Run the bot
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid token provided. Please check your configuration.")


