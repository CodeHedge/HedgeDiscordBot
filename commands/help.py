from discord.ext import commands
import discord

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = CustomHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

class CustomHelpCommand(commands.HelpCommand):
    """Custom help command implementation with better formatting"""
    
    async def send_bot_help(self, mapping):
        """Send help for all commands"""
        embed = discord.Embed(
            title="Bot Commands",
            description="Here are all available commands. Type `!help [command]` for more information about a specific command.",
            color=discord.Color.blue()
        )
        
        # Group commands by cog/category
        for cog, commands in mapping.items():
            filtered = await self.filter_commands(commands, sort=True)
            if filtered:
                cog_name = getattr(cog, "qualified_name", "Other")
                
                # Define emoji for different cog types
                emoji = "📋"  # Default
                if cog_name == "BasicCommands":
                    cog_name = "Basic Commands"
                    emoji = "🔧"
                elif cog_name == "AICommands":
                    cog_name = "AI Commands"
                    emoji = "🤖"
                elif cog_name == "ModerationCommands":
                    cog_name = "Moderation Commands"
                    emoji = "🛡️"
                elif cog_name == "UtilityCommands":
                    cog_name = "Utility Commands"
                    emoji = "🔧"
                elif cog_name == "ReminderCommands":
                    cog_name = "Reminder Commands"
                    emoji = "⏰"
                elif cog_name == "AIAnalysisCommands":
                    cog_name = "AI Analysis Commands"
                    emoji = "📊"
                
                command_list = "\n".join(f"`!{cmd.name}`" for cmd in filtered)
                embed.add_field(name=f"{emoji} {cog_name}", value=command_list, inline=False)
        
        # Add some footer information
        embed.set_footer(text="Type !help [command] for detailed information on a command")
        
        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command):
        """Send help for a specific command"""
        embed = discord.Embed(
            title=f"Help: !{command.name}",
            description=command.help or "No description available",
            color=discord.Color.green()
        )
        
        # Add usage information
        usage = f"!{command.name}"
        if command.signature:
            usage += f" {command.signature}"
        embed.add_field(name="Usage", value=f"`{usage}`", inline=False)
        
        # Add examples for specific commands
        if command.name == "remind":
            embed.add_field(
                name="Examples",
                value=(
                    "`!remind 1h Check the oven`\n"
                    "`!remind 30m Call mom`\n"
                    "`!remind 2d Submit report`"
                ),
                inline=False
            )
        elif command.name == "summarize":
            embed.add_field(
                name="Examples",
                value=(
                    "`!summarize` - Summarize last 25 messages\n"
                    "`!summarize 50` - Summarize last 50 messages"
                ),
                inline=False
            )
        elif command.name == "analyze":
            embed.add_field(
                name="Examples",
                value=(
                    "`!analyze` - Analyze your own messages from the past week\n"
                    "`!analyze @User` - Analyze mentioned user's messages\n"
                    "`!analyze @User 14` - Analyze messages from the past 14 days"
                ),
                inline=False
            )
        elif command.name == "userinfo":
            embed.add_field(
                name="Examples",
                value=(
                    "`!userinfo` - Show your own info\n"
                    "`!userinfo @User` - Show info about mentioned user"
                ),
                inline=False
            )
            
        # Add aliases if any
        if command.aliases:
            aliases = ", ".join(f"`!{alias}`" for alias in command.aliases)
            embed.add_field(name="Aliases", value=aliases, inline=False)
            
        embed.set_footer(text="<required> [optional]")
        
        await self.get_destination().send(embed=embed)
        
    async def send_error_message(self, error):
        """Send error message when command is not found"""
        embed = discord.Embed(
            title="Help Error",
            description=error,
            color=discord.Color.red()
        )
        await self.get_destination().send(embed=embed)
        
    async def send_cog_help(self, cog):
        """Send help for a specific category/cog"""
        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        if filtered:
            cog_name = cog.qualified_name
            
            # Make the cog name more readable
            if cog_name == "BasicCommands":
                display_name = "Basic Commands"
            elif cog_name == "AICommands":
                display_name = "AI Commands"
            elif cog_name == "ModerationCommands":
                display_name = "Moderation Commands"
            elif cog_name == "UtilityCommands":
                display_name = "Utility Commands"
            elif cog_name == "ReminderCommands":
                display_name = "Reminder Commands"
            elif cog_name == "AIAnalysisCommands":
                display_name = "AI Analysis Commands"
            else:
                display_name = cog_name
                
            embed = discord.Embed(
                title=f"{display_name} Help",
                description=cog.description or "Commands in this category:",
                color=discord.Color.blue()
            )
            
            for command in filtered:
                embed.add_field(
                    name=f"!{command.name}",
                    value=command.help or "No description available",
                    inline=False
                )
                
            await self.get_destination().send(embed=embed) 