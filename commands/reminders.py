from discord.ext import commands, tasks
import discord
import asyncio
import re
from datetime import datetime, timedelta
import json
import os
import logging

logger = logging.getLogger(__name__)

class Reminder:
    def __init__(self, user_id, channel_id, message, end_time, reminder_id):
        self.user_id = user_id
        self.channel_id = channel_id
        self.message = message
        self.end_time = end_time
        self.id = reminder_id

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "channel_id": self.channel_id,
            "message": self.message,
            "end_time": self.end_time.isoformat(),
            "id": self.id
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["user_id"],
            data["channel_id"],
            data["message"],
            datetime.fromisoformat(data["end_time"]),
            data["id"]
        )

class ReminderCommands(commands.Cog):
    """Commands for setting and managing reminders"""
    
    def __init__(self, bot):
        self.bot = bot
        self.reminders = []
        self.next_id = 1
        self.reminders_file = "reminders.json"
        self.load_reminders()
        self.check_reminders.start()
        logger.info("ReminderCommands cog initialized")

    def cog_unload(self):
        self.check_reminders.cancel()
        logger.info("ReminderCommands cog unloaded")

    def load_reminders(self):
        """Load saved reminders from file"""
        if os.path.exists(self.reminders_file):
            try:
                with open(self.reminders_file, 'r') as f:
                    data = json.load(f)
                    self.reminders = [Reminder.from_dict(reminder) for reminder in data["reminders"]]
                    self.next_id = data["next_id"]
                logger.info(f"Loaded {len(self.reminders)} reminders")
            except Exception as e:
                logger.error(f"Error loading reminders: {e}")
                self.reminders = []
                self.next_id = 1

    def save_reminders(self):
        """Save current reminders to file"""
        try:
            with open(self.reminders_file, 'w') as f:
                data = {
                    "reminders": [reminder.to_dict() for reminder in self.reminders],
                    "next_id": self.next_id
                }
                json.dump(data, f, indent=4)
            logger.info(f"Saved {len(self.reminders)} reminders")
        except Exception as e:
            logger.error(f"Error saving reminders: {e}")

    @tasks.loop(seconds=30)
    async def check_reminders(self):
        """Check for reminders that need to be sent"""
        now = datetime.utcnow()
        to_remove = []

        for reminder in self.reminders:
            if reminder.end_time <= now:
                # Get the channel and send the reminder
                channel = self.bot.get_channel(reminder.channel_id)
                if channel:
                    try:
                        await channel.send(f"<@{reminder.user_id}> Reminder: {reminder.message}")
                        logger.info(f"Sent reminder {reminder.id} to user {reminder.user_id}")
                    except Exception as e:
                        logger.error(f"Error sending reminder: {e}")
                else:
                    logger.warning(f"Could not find channel {reminder.channel_id} for reminder {reminder.id}")
                
                to_remove.append(reminder)

        # Remove sent reminders
        for reminder in to_remove:
            self.reminders.remove(reminder)
            
        if to_remove:
            self.save_reminders()

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

    @commands.command(
        name="remind", 
        brief="Set a timed reminder",
        help="Sets a reminder for the specified time. Format: !remind [time] [message]. Time can be specified as 30s (seconds), 10m (minutes), 2h (hours), or 1d (days)."
    )
    async def remind(self, ctx, time_str: str, *, reminder_text: str):
        """
        Set a reminder. Examples:
        !remind 1h Check the oven
        !remind 30m Call mom
        !remind 2d Submit report
        """
        # Parse the time string
        match = re.match(r'(\d+)([smhd])', time_str)
        if not match:
            await ctx.send("Invalid time format. Use e.g. 1h, 30m, 2d (s=seconds, m=minutes, h=hours, d=days)")
            return

        amount, unit = match.groups()
        amount = int(amount)
        
        # Convert to seconds
        seconds = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400
        }[unit] * amount
        
        # Limit reminder duration to 30 days
        if seconds > 2592000:  # 30 days
            await ctx.send("Reminder time too long. Maximum is 30 days.")
            return
            
        end_time = datetime.utcnow() + timedelta(seconds=seconds)
        
        # Create and store the reminder
        reminder = Reminder(
            ctx.author.id,
            ctx.channel.id,
            reminder_text,
            end_time,
            self.next_id
        )
        
        self.reminders.append(reminder)
        self.next_id += 1
        self.save_reminders()
        
        # Format confirmation message
        time_units = {
            's': 'second',
            'm': 'minute',
            'h': 'hour',
            'd': 'day'
        }
        time_unit = time_units[unit] + ('s' if amount != 1 else '')
        
        await ctx.send(f"I'll remind you about **{reminder_text}** in **{amount} {time_unit}**.")
        logger.info(f"Set reminder {reminder.id} for user {ctx.author.id} at {end_time}")

    @commands.command(
        name="reminders",
        brief="List your reminders",
        help="Lists all your active reminders with their IDs and remaining time."
    )
    async def reminders(self, ctx):
        """List all your active reminders"""
        user_reminders = [r for r in self.reminders if r.user_id == ctx.author.id]
        
        if not user_reminders:
            await ctx.send("You don't have any active reminders.")
            return
            
        embed = discord.Embed(
            title="Your Reminders",
            description=f"You have {len(user_reminders)} active reminder(s).",
            color=discord.Color.blue()
        )
        
        for reminder in user_reminders:
            time_left = reminder.end_time - datetime.utcnow()
            hours, remainder = divmod(time_left.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            time_str = ""
            if hours > 0:
                time_str += f"{int(hours)} hours "
            if minutes > 0:
                time_str += f"{int(minutes)} minutes "
            if seconds > 0 and hours == 0:  # Only show seconds if less than an hour
                time_str += f"{int(seconds)} seconds"
                
            time_str = time_str.strip() or "Now"
            
            embed.add_field(
                name=f"ID: {reminder.id} - {time_str}",
                value=reminder.message,
                inline=False
            )
            
        await ctx.send(embed=embed)
        
    @commands.command(
        name="cancel_reminder",
        brief="Cancel a reminder",
        help="Cancels a specific reminder by its ID. Use !reminders to see IDs of your active reminders."
    )
    async def cancel_reminder(self, ctx, reminder_id: int):
        """Cancel a specific reminder by ID"""
        # Find the reminder
        reminder = next((r for r in self.reminders if r.id == reminder_id and r.user_id == ctx.author.id), None)
        
        if not reminder:
            await ctx.send(f"Could not find reminder with ID {reminder_id}.")
            return
            
        self.reminders.remove(reminder)
        self.save_reminders()
        
        await ctx.send(f"Canceled reminder: {reminder.message}")
        logger.info(f"Canceled reminder {reminder_id} for user {ctx.author.id}") 