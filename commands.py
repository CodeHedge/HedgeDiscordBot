from discord.ext import commands
import discord

def setup_commands(bot):
    @bot.command()
    async def ping(ctx):
        """A simple ping command."""
        await ctx.send("Pong! 🏓")

    @bot.command()
    async def info(ctx):
        """Send bot information as an embed."""
        embed = discord.Embed(
            title="Bot Information",
            description="This is a sample embed message.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Author", value=ctx.author.name, inline=False)

        # Check if the channel is a DM or a guild channel
        if isinstance(ctx.channel, discord.DMChannel):
            embed.add_field(name="Channel", value="Direct Message", inline=False)
        else:
            embed.add_field(name="Channel", value=ctx.channel.name, inline=False)

        embed.set_footer(text="HedgeDiscordBot")
        await ctx.send(embed=embed)