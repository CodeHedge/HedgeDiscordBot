from discord.ext import commands
import discord
from commands import registry

@registry.register
class BasicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """A simple ping command."""
        await ctx.send("Pong! 🏓")

    @commands.command()
    async def info(self, ctx):
        """Send bot information as an embed."""
        embed = discord.Embed(
            title="Bot Information",
            description="Im hedges bot. Working on more features. I auto update when i get pushed too. Cool.....",
            color=discord.Color.blue()
        )
        embed.add_field(name="Author", value=ctx.author.name, inline=False)

        if isinstance(ctx.channel, discord.DMChannel):
            embed.add_field(name="Channel", value="Direct Message", inline=False)
        else:
            embed.add_field(name="Channel", value=ctx.channel.name, inline=False)

        embed.set_footer(text="HedgeDiscordBot")
        await ctx.send(embed=embed) 