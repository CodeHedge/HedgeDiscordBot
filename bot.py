#discord bot that monitors messages in a list of channels

import discord
from discord.ext import commands
import logging
import asyncio
from config import load_config, load_moderation, member_manager
from ai import moderate_message
import os
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Load the configuration
config = load_config()
TOKEN = config['token']
CHANNELS = config['channels']
EXCLUDED_USERS = config.get('excluded_users', [])

# Load the moderation file
load_moderation()

# Initialize Discord bot with all necessary intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Explicitly load each cog
async def load_extensions():
    try:
        # Import cog classes
        from commands.basic import BasicCommands
        from commands.ai_commands import AICommands
        from commands.moderation import ModerationCommands
        from commands.utility import UtilityCommands
        from commands.reminders import ReminderCommands
        from commands.ai_analysis import AIAnalysisCommands
        from commands.help import HelpCommand
        from commands.member_commands import MemberCommands
        
        # Add cogs one by one with explicit error handling
        cogs_to_load = [
            (BasicCommands, "BasicCommands"),
            (AICommands, "AICommands"),
            (ModerationCommands, "ModerationCommands"),
            (UtilityCommands, "UtilityCommands"),
            (ReminderCommands, "ReminderCommands"),
            (AIAnalysisCommands, "AIAnalysisCommands"),
            (HelpCommand, "HelpCommand"),
            (MemberCommands, "MemberCommands")
        ]
        
        for cog_class, cog_name in cogs_to_load:
            try:
                await bot.add_cog(cog_class(bot))
                logger.info(f"Successfully loaded cog: {cog_name}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog_name}: {e}")
                logger.error(traceback.format_exc())
                
        logger.info("All cogs have been processed")
    except Exception as e:
        logger.error(f"Error during extension loading: {e}")
        logger.error(traceback.format_exc())

@bot.event
async def on_ready():
    """Called when the bot is ready"""
    logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    
    # Load all extensions/cogs
    await load_extensions()
    
    # Log all registered commands for debugging
    commands_list = [command.name for command in bot.commands]
    logger.info(f"Registered commands: {', '.join(commands_list)}")
    
    logger.info("Bot is ready and connected to Discord!")

@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Check if the message is from a monitored channel (only for non-DM messages)
    if message.guild and str(message.channel.id) in CHANNELS:
        logger.info(f"Message received in monitored channel {message.channel.name}: {message.content}")

        # Run the message through the moderation API
        await moderate_message(message.content, str(message.author))

        # Example: Reply to the message
        if "hello bot" in message.content.lower():
            await message.channel.send(f"Hello, {message.author.mention}!")

    # Process commands
    await bot.process_commands(message)

# Run the bot
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid token provided. Please check your configuration.")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        logger.error(traceback.format_exc())


