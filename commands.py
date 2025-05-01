from discord.ext import commands
import discord
import openai  # pip install openai
import asyncio
import ai
from config import load_config  # Reuse the load_config function
from ai import process_ai_request  # Import the new AI logic
import json
import os
from datetime import datetime, timedelta

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
    async def prompt(ctx, *, prompt: str):
        if hasattr(ctx.channel, "trigger_typing"):
            await ctx.channel.trigger_typing()
        answer = await process_ai_request(prompt)
        await ctx.send(answer)

    @bot.command()
    async def offenses(ctx):
        """List all users and their offenses."""
        moderation_path = 'moderation.json'
        if not os.path.exists(moderation_path):
            await ctx.send("No moderation data found.")
            return

        with open(moderation_path, 'r') as f:
            data = json.load(f)

        if not data:
            await ctx.send("No offenses recorded.")
            return

        embed = discord.Embed(
            title="User Offenses",
            description="List of users and their offenses:",
            color=discord.Color.red()
        )

        for username, offenses in data.items():
            offense_list = "\n".join([f"{category}: {count}" for category, count in offenses.items()])
            embed.add_field(name=username, value=offense_list, inline=False)

        await ctx.send(embed=embed)

    @bot.command()
    async def offenses_user(ctx, username: str):
        """List offenses for a specific user."""
        moderation_path = 'moderation.json'
        if not os.path.exists(moderation_path):
            await ctx.send("No moderation data found.")
            return

        with open(moderation_path, 'r') as f:
            data = json.load(f)

        if username not in data:
            await ctx.send(f"No offenses recorded for user: {username}")
            return

        offenses = data[username]
        offense_list = "\n".join([f"{category}: {count}" for category, count in offenses.items()])

        embed = discord.Embed(
            title=f"Offenses for {username}",
            description=offense_list,
            color=discord.Color.red()
        )

        await ctx.send(embed=embed)

    @bot.command()
    async def add_channel(ctx, channel_id: int):
        """Add a channel to the monitored channels."""
        config = load_config()
        if str(channel_id) not in config['channels']:
            config['channels'].append(str(channel_id))
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)
            await ctx.send(f"Channel {channel_id} added to the monitored channels.")
        else:
            await ctx.send(f"Channel {channel_id} is already in the monitored channels.")

    @bot.command()
    async def scan_history(ctx, days: int):
        """
        Scan the last x days in all monitored channels.
        This command clears the moderation file before starting.
        """
        # Clear the moderation.json file.
        moderation_path = 'moderation.json'
        with open(moderation_path, 'w') as f:
            json.dump({}, f, indent=4)
        await ctx.send("Cleared previous moderation records. Beginning history scan...")

        config = load_config()
        cutoff_time = datetime.utcnow() - timedelta(days=days)

        for channel_id in config['channels']:
            channel = bot.get_channel(int(channel_id))
            if channel:
                await ctx.send(f"Scanning channel: {channel.name}")
                async for message in channel.history(after=cutoff_time, oldest_first=True):
                    # Skip if message has no content.
                    if not message.content:
                        continue
                    # Run each message through the moderation API.
                    await ai.moderate_message(message.content, str(message.author))
            else:
                await ctx.send(f"Could not find channel with ID {channel_id}")

        await ctx.send("Finished scanning message history.")
    
    @bot.command()
    async def commands(ctx):
        """List all commands."""
        embed = discord.Embed(
            title="Available Commands",
            description="Here are the commands you can use:",
            color=discord.Color.green()
        )
        commands_list = [
            "!ping - Check if the bot is alive.",
            "!info - Get information about the bot.",
            "!prompt <your prompt> - Send a prompt to the AI.",
            "!offenses - List all users and their offenses.",
            "!offenses_user <username> - List offenses for a specific user.",
            "!add_channel <channel_id> - Add a channel to the monitored channels.",
            "!scan_history <days> - Scan the last x days in all monitored channels."
        ]
        embed.add_field(name="Commands", value="\n".join(commands_list), inline=False)
        await ctx.send(embed=embed)