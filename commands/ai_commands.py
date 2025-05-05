from discord.ext import commands
from ai import process_ai_request

class AICommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def prompt(self, ctx, *, prompt: str):
        """Process an AI prompt and return the response."""
        if hasattr(ctx.channel, "trigger_typing"):
            await ctx.channel.trigger_typing()
        answer = await process_ai_request(prompt)
        await ctx.send(answer) 