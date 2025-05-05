import discord
from discord.ext import commands
import logging
from config import load_config
from ai import moderate_message

logger = logging.getLogger(__name__)

class EventHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()
        self.channels = self.config['channels']
        self.excluded_users = self.config.get('excluded_users', [])

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"Logged in as {self.bot.user} (ID: {self.bot.user.id})")
        logger.info("Bot is ready and connected to Discord!")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from the bot itself
        if message.author == self.bot.user:
            return

        # Check if the message is from a monitored channel (only for non-DM messages)
        if message.guild and str(message.channel.id) in self.channels:
            logger.info(f"Message received in monitored channel {message.channel.name}: {message.content}")

            # Run the message through the moderation API
            await moderate_message(message.content, str(message.author))

            # Example: Reply to the message
            if "hello bot" in message.content.lower():
                await message.channel.send(f"Hello, {message.author.mention}!")

        # Process commands regardless of the channel type (guild or DM)
        await self.bot.process_commands(message) 