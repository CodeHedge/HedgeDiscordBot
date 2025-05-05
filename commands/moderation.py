from discord.ext import commands
import discord
import json
import os
from config import load_config
from ai import moderate_message

class ModerationCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()
        self.sudo_users = self.config.get("sudo", [])

    @commands.command()
    async def offenses(self, ctx):
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

    @commands.command()
    async def offenses_user(self, ctx, username: str):
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

    @commands.command()
    async def add_channel(self, ctx, channel_id: int):
        """Add a channel to the monitored channels."""
        if ctx.author.id not in self.sudo_users:
            await ctx.send("You do not have permission to use this command.")
            return

        if str(channel_id) not in self.config['channels']:
            self.config['channels'].append(str(channel_id))
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=4)
            await ctx.send(f"Channel {channel_id} added to the monitored channels.")
        else:
            await ctx.send(f"Channel {channel_id} is already in the monitored channels.")

    @commands.command()
    async def remove_channel(self, ctx, channel_id: int):
        """Remove a channel from the monitored channels."""
        if ctx.author.id not in self.sudo_users:
            await ctx.send("You do not have permission to use this command.")
            return

        if str(channel_id) in self.config['channels']:
            self.config['channels'].remove(str(channel_id))
            with open('config.json', 'w') as f:
                json.dump(self.config, f, indent=4)
            await ctx.send(f"Channel {channel_id} removed from the monitored channels.")
        else:
            await ctx.send(f"Channel {channel_id} is not in the monitored channels.")

    @commands.command()
    async def scan_history(self, ctx, quantity: int):
        """Scan the last x messages in all monitored channels."""
        if ctx.author.id not in self.sudo_users:
            await ctx.send("You do not have permission to use this command.")
            return

        # Clear the moderation.json file
        moderation_path = 'moderation.json'
        with open(moderation_path, 'w') as f:
            json.dump({}, f, indent=4)
        await ctx.send("Cleared previous moderation records. Beginning history scan...")

        processed_texts = []
        moderation_count = 0

        for channel_id in self.config['channels']:
            channel = self.bot.get_channel(int(channel_id))
            if channel:
                await ctx.send(f"Scanning channel: {channel.name}")
                async for message in channel.history(limit=quantity, oldest_first=True):
                    if not message.content:
                        continue
                    processed_texts.append(message.content)
                    
                    # Send to moderation API
                    try:
                        await moderate_message(message.content, str(message.author))
                        moderation_count += 1
                    except Exception as e:
                        await ctx.send(f"Error moderating message: {e}")
            else:
                await ctx.send(f"Could not find channel with ID {channel_id}")

        await ctx.send(f"Processed {moderation_count} messages for moderation.")

        if processed_texts:
            text_summary = "\n\n".join(processed_texts)
            if len(text_summary) > 1900:
                text_summary = text_summary[:1900] + "\n...[truncated]"
            embed = discord.Embed(
                title="Scanned Message Texts",
                description=text_summary,
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("No messages were processed for moderation.")

        await ctx.send("Finished scanning message history.") 