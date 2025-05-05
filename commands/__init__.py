from discord.ext import commands
from typing import List, Type
import logging

logger = logging.getLogger(__name__)

class CommandRegistry:
    def __init__(self):
        self.commands: List[Type[commands.Cog]] = []

    def register(self, command_class: Type[commands.Cog]):
        """Register a new command class"""
        self.commands.append(command_class)
        logger.info(f"Registered command class: {command_class.__name__}")

    def setup_commands(self, bot: commands.Bot):
        """Setup all registered commands"""
        for command_class in self.commands:
            bot.add_cog(command_class(bot))
            logger.info(f"Added cog: {command_class.__name__}")

# Create a global registry instance
registry = CommandRegistry() 