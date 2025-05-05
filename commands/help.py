from discord.ext import commands
import discord
import logging
import random

logger = logging.getLogger(__name__)

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Setting up custom help command")
        self._original_help_command = bot.help_command
        bot.help_command = CustomHelpCommand()
        bot.help_command.cog = self
        logger.info("Custom help command set up")

    def cog_unload(self):
        self.bot.help_command = self._original_help_command
        logger.info("Custom help command unloaded")

class CustomHelpCommand(commands.HelpCommand):
    """Custom help command implementation with better formatting"""
    
    # Category colors for visual distinction
    CATEGORY_COLORS = {
        "BasicCommands": 0x3498db,      # Blue
        "AICommands": 0x9b59b6,         # Purple
        "ModerationCommands": 0xe74c3c, # Red
        "UtilityCommands": 0x2ecc71,    # Green
        "ReminderCommands": 0xf1c40f,   # Yellow
        "AIAnalysisCommands": 0xe67e22, # Orange
        "HelpCommand": 0x1abc9c,        # Teal
        "Other": 0x95a5a6               # Gray
    }
    
    # Category icons for better visual identification
    CATEGORY_ICONS = {
        "BasicCommands": "🔹",
        "AICommands": "🤖",
        "ModerationCommands": "🛡️",
        "UtilityCommands": "🔧",
        "ReminderCommands": "⏰",
        "AIAnalysisCommands": "📊",
        "HelpCommand": "❔",
        "Other": "📋"
    }
    
    # Category descriptions
    CATEGORY_DESCRIPTIONS = {
        "BasicCommands": "Essential bot commands",
        "AICommands": "Interact with the AI assistant",
        "ModerationCommands": "Server moderation and management",
        "UtilityCommands": "Useful server and user information",
        "ReminderCommands": "Set and manage reminders",
        "AIAnalysisCommands": "Analyze messages and conversations with AI",
        "HelpCommand": "Get help with bot commands",
        "Other": "Miscellaneous commands"
    }
    
    async def send_bot_help(self, mapping):
        """Send help for all commands"""
        # Random tip to show in the help message
        tips = [
            "You can use `!help [command]` to get detailed information about a specific command.",
            "Try using the `!analyze` command to see insights about your messaging style.",
            "Set reminders with `!remind 1h Do something` to get notified later.",
            "Use `!summarize` to get an AI-generated summary of recent conversation.",
            "Check server stats with `!serverinfo` or user info with `!userinfo`."
        ]
        random_tip = random.choice(tips)
        
        embed = discord.Embed(
            title="📚 Bot Commands",
            description=f"Here are all available commands grouped by category.\n\n**Tip:** {random_tip}",
            color=discord.Color.blue()
        )
        
        # Add bot avatar if available
        if self.context.bot.user.avatar:
            embed.set_thumbnail(url=self.context.bot.user.avatar.url)
        
        # Group commands by cog/category
        for cog, cmds in mapping.items():
            filtered = await self.filter_commands(cmds, sort=True)
            if not filtered:
                continue
                
            cog_name = getattr(cog, "qualified_name", "Other")
            logger.info(f"Processing commands for cog: {cog_name}, found {len(filtered)} commands")
            
            # Get display name, icon and color for this category
            icon = self.CATEGORY_ICONS.get(cog_name, "📋")
            display_name = self._get_display_name(cog_name)
            
            # Format each command with its brief description
            command_list = []
            for cmd in filtered:
                brief = cmd.brief or cmd.short_doc or "No description"
                command_list.append(f"`!{cmd.name}` - {brief}")
            
            if not command_list:
                continue
                
            # Join commands with newlines
            value = "\n".join(command_list)
            
            # Add field to embed with icon and formatted name
            embed.add_field(
                name=f"{icon} {display_name}",
                value=value,
                inline=False
            )
        
        # Add footer with command count
        total_commands = len(set(cmd for cmds in mapping.values() for cmd in cmds))
        embed.set_footer(text=f"{total_commands} commands available • Type !help [command] for details")
        
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        """Send help for a specific command"""
        logger.info(f"Showing help for command: {command.name}")
        
        # Find the cog this command belongs to
        cog_name = command.cog_name if command.cog_name else "Other"
        color = self.CATEGORY_COLORS.get(cog_name, 0x95a5a6)
        
        embed = discord.Embed(
            title=f"Command: !{command.name}",
            description=command.help or command.description or "No detailed description available.",
            color=color
        )
        
        # Add usage section with code formatting
        usage = f"!{command.name}"
        if command.signature:
            usage += f" {command.signature}"
        embed.add_field(name="📝 Usage", value=f"```{usage}```", inline=False)
        
        # Add examples for specific commands
        if command.name == "remind":
            embed.add_field(
                name="📋 Examples",
                value=(
                    "`!remind 1h Check the oven`\n"
                    "`!remind 30m Call mom`\n"
                    "`!remind 2d Submit report`"
                ),
                inline=False
            )
        elif command.name == "summarize":
            embed.add_field(
                name="📋 Examples",
                value=(
                    "`!summarize` - Summarize last 25 messages\n"
                    "`!summarize 50` - Summarize last 50 messages"
                ),
                inline=False
            )
        elif command.name == "analyze":
            embed.add_field(
                name="📋 Examples",
                value=(
                    "`!analyze` - Analyze your own messages from the past week\n"
                    "`!analyze @User` - Analyze mentioned user's messages\n"
                    "`!analyze @User 14` - Analyze messages from the past 14 days"
                ),
                inline=False
            )
        elif command.name == "userinfo":
            embed.add_field(
                name="📋 Examples",
                value=(
                    "`!userinfo` - Show your own info\n"
                    "`!userinfo @User` - Show info about mentioned user"
                ),
                inline=False
            )
            
        # Add aliases if any
        if command.aliases:
            aliases = ", ".join(f"`!{alias}`" for alias in command.aliases)
            embed.add_field(name="🔄 Aliases", value=aliases, inline=False)
            
        # Add category
        category_icon = self.CATEGORY_ICONS.get(cog_name, "📋")
        category_name = self._get_display_name(cog_name)
        embed.add_field(name="📁 Category", value=f"{category_icon} {category_name}", inline=True)
        
        # Add cooldown if any
        if command._buckets and command._buckets._cooldown:
            cooldown = command._buckets._cooldown
            embed.add_field(
                name="⏱️ Cooldown", 
                value=f"{cooldown.rate} uses every {cooldown.per:.0f} seconds", 
                inline=True
            )
            
        embed.set_footer(text="<required> [optional]")
        
        await self.get_destination().send(embed=embed)
        
    async def send_error_message(self, error):
        """Send error message when command is not found"""
        logger.warning(f"Help error: {error}")
        embed = discord.Embed(
            title="❌ Help Error",
            description=error,
            color=discord.Color.red()
        )
        embed.set_footer(text="Type !help to see all available commands")
        await self.get_destination().send(embed=embed)
        
    async def send_cog_help(self, cog):
        """Send help for a specific category/cog"""
        logger.info(f"Showing help for cog: {cog.qualified_name}")
        
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        if not filtered:
            logger.warning(f"No commands found in cog {cog.qualified_name}")
            await self.get_destination().send(f"No commands available in the {cog.qualified_name} category.")
            return
            
        cog_name = cog.qualified_name
        color = self.CATEGORY_COLORS.get(cog_name, 0x95a5a6)
        icon = self.CATEGORY_ICONS.get(cog_name, "📋")
        display_name = self._get_display_name(cog_name)
        description = self.CATEGORY_DESCRIPTIONS.get(cog_name, "Commands in this category")
        
        # Get cog description if available
        if hasattr(cog, "description") and cog.description:
            description = cog.description
            
        embed = discord.Embed(
            title=f"{icon} {display_name} Commands",
            description=description,
            color=color
        )
        
        # Add each command with its help text
        for command in filtered:
            name = f"!{command.name}"
            value = command.help or command.brief or command.short_doc or "No description available"
            
            # For shorter help text, also include usage
            if len(value) < 80:
                usage = command.signature if command.signature else ""
                if usage:
                    value += f"\n\nUsage: `!{command.name} {usage}`"
                    
            embed.add_field(
                name=name,
                value=value,
                inline=False
            )
        
        # Footer with command count
        embed.set_footer(text=f"{len(filtered)} commands in this category • Type !help [command] for details")
        
        await self.get_destination().send(embed=embed)
        
    def _get_display_name(self, cog_name):
        """Convert cog name to a readable display name"""
        if cog_name == "BasicCommands":
            return "Basic Commands"
        elif cog_name == "AICommands":
            return "AI Commands"
        elif cog_name == "ModerationCommands":
            return "Moderation Commands"
        elif cog_name == "UtilityCommands":
            return "Utility Commands"
        elif cog_name == "ReminderCommands":
            return "Reminder Commands"
        elif cog_name == "AIAnalysisCommands":
            return "AI Analysis Commands"
        elif cog_name == "HelpCommand":
            return "Help Commands"
        else:
            return cog_name 