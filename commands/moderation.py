from discord.ext import commands
import discord
import json
import os
from config import load_config
from ai import moderate_message
from helper import get_recent_offensive_messages
from datetime import datetime

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
        """List offenses for a specific user with recent offensive messages."""
        moderation_path = 'moderation.json'
        if not os.path.exists(moderation_path):
            await ctx.send("No moderation data found.")
            return

        with open(moderation_path, 'r') as f:
            data = json.load(f)

        if username not in data:
            await ctx.send(f"No offenses recorded for user: {username}")
            return

        # Create a new embed for just this user
        offenses = data[username]
        offense_list = "\n".join([f"{category}: {count}" for category, count in offenses.items()])

        embed = discord.Embed(
            title=f"Offenses for {username}",
            description=offense_list,
            color=discord.Color.red()
        )

        # Get and display recent offensive messages
        recent_messages = get_recent_offensive_messages(username, 3)
        
        if recent_messages:
            message_text = ""
            for i, msg in enumerate(recent_messages):
                # Format the timestamp
                try:
                    timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                except:
                    timestamp = msg["timestamp"]
                
                message_text += f"**Message {i+1}** - {msg['category']} ({timestamp})\n"
                message_text += f"{msg['content']}\n\n"
            
            # Add messages as a single field to keep them together
            embed.add_field(
                name="Recent Offensive Messages",
                value=message_text if message_text else "No message content available",
                inline=False
            )
        else:
            embed.add_field(
                name="Recent Messages", 
                value="No offensive messages recorded for this user", 
                inline=False
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
        offense_messages_path = 'offense_messages.json'
        with open(moderation_path, 'w') as f:
            json.dump({}, f, indent=4)
        with open(offense_messages_path, 'w') as f:
            json.dump({}, f, indent=4)
        await ctx.send("Cleared previous moderation records. Beginning history scan...")

        processed_texts = []
        moderation_count = 0
        flagged_count = 0

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
                        
                        # Check if any offenses were recorded for this message
                        if os.path.exists(offense_messages_path):
                            with open(offense_messages_path, 'r') as f:
                                messages_data = json.load(f)
                                if str(message.author) in messages_data:
                                    for msg in messages_data[str(message.author)]:
                                        # Rough check if this is the same message
                                        if message.content == msg.get("content"):
                                            flagged_count += 1
                                            break
                    except Exception as e:
                        await ctx.send(f"Error moderating message: {e}")
            else:
                await ctx.send(f"Could not find channel with ID {channel_id}")

        await ctx.send(f"Processed {moderation_count} messages for moderation. Found {flagged_count} flagged messages.")

        if processed_texts:
            total_messages = len(processed_texts)
            text_summary = f"Scanned {total_messages} messages total.\n\n"
            
            # Only show a sample of processed texts
            sample_texts = processed_texts[:5]
            text_summary += "Sample of scanned messages:\n\n" + "\n\n".join(sample_texts)
            
            if len(text_summary) > 1900:
                text_summary = text_summary[:1900] + "\n...[truncated]"
            
            embed = discord.Embed(
                title="Scan Summary",
                description=text_summary,
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("No messages were processed for moderation.")

        await ctx.send("Finished scanning message history.")

    @commands.command()
    async def debug_messages(self, ctx):
        """Debug command to view the raw offense_messages.json file."""
        if ctx.author.id not in self.sudo_users:
            await ctx.send("You do not have permission to use this command.")
            return
            
        messages_path = 'offense_messages.json'
        if not os.path.exists(messages_path):
            await ctx.send("No offense messages file found.")
            return
            
        try:
            with open(messages_path, 'r') as f:
                data = json.load(f)
                
            # Create a readable summary
            summary = "Offense Messages Debug:\n\n"
            
            if not data:
                summary += "No data in offense_messages.json"
            else:
                summary += f"Users with stored messages: {list(data.keys())}\n\n"
                
                for username, messages in data.items():
                    summary += f"User: {username} - {len(messages)} messages\n"
                    
                    if messages:
                        # Show first message as example
                        first_msg = messages[0]
                        summary += f"Example: {first_msg.get('category')} - {first_msg.get('content')[:50]}...\n\n"
            
            # Split into chunks if needed
            if len(summary) > 1900:
                chunks = [summary[i:i+1900] for i in range(0, len(summary), 1900)]
                for chunk in chunks:
                    await ctx.send(f"```\n{chunk}\n```")
            else:
                await ctx.send(f"```\n{summary}\n```")
                
        except Exception as e:
            await ctx.send(f"Error reading offense messages file: {e}") 