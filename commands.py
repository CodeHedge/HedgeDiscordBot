from discord.ext import commands
import discord
import openai  # pip install openai
import asyncio
from config import load_config  # Reuse the load_config function
from ai import process_ai_request  # Import the new AI logic

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
            description="Im hedges bot. Working on more features. I auto update when i get pushed too. Cool.....",
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

    @bot.command()
    async def ai(ctx, *, prompt: str):
        if hasattr(ctx.channel, "trigger_typing"):
            await ctx.channel.trigger_typing()
        answer = await process_ai_request(prompt)
        await ctx.send(answer)