from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

def setup_commands(bot: commands.Bot):
    """Setup all commands for the bot"""
    # Import and register all command modules
    from . import basic, ai_commands, moderation
    
    # Add all cogs
    bot.add_cog(basic.BasicCommands(bot))
    bot.add_cog(ai_commands.AICommands(bot))
    bot.add_cog(moderation.ModerationCommands(bot))
    
    logger.info("All commands have been loaded and registered") 