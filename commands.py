from discord.ext import commands

def setup_commands(bot):
    @bot.command()
    async def ping(ctx):
        """A simple ping command."""
        await ctx.send("Pong! 🏓")