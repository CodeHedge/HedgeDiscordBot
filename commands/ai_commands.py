from discord.ext import commands
import discord
from ai import process_ai_request
import json
import logging
from datetime import datetime, timedelta
import re
import random
from config import member_manager

logger = logging.getLogger(__name__)


class AICommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("AICommands cog initialized")

        # Toggle for _hedge protection feature
        self.hedge_protection_enabled = False

        # Collection of dynamic roast scenarios
        self.roast_scenarios = [
            "Roast like a disappointed parent.",
            "Roast like a stand-up comic responding to a heckler.",
            "Roast them like an FBI profiler diagnosing a sociopath.",
            "Roast their hobbies like a sarcastic sibling.",
            "Roast like a passive-aggressive Yelp review.",
            "Roast their message repetition like it's a cry for help.",
            "Roast like a sentient AI sick of their existence.",
            "Roast their confidence like it was built on sand during high tide.",
            "Roast them like their life is a group project and they did nothing.",
            "Roast their attention span like a goldfish with commitment issues.",
            "Roast them like a documentary narrator explaining the downfall of a once-promising idiot.",
            "Roast them like a group chat admin who's about to kick them for vibes alone.",
            "Roast like a lawyer delivering closing arguments on why they should be banned from social interaction.",
            "Roast them like their personality was crowd-sourced from bad Reddit takes.",
            "Roast them like a life coach who just gave up mid-session.",
            "Roast them like you're the human embodiment of the lounge server.",
        ]

    @commands.command()
    async def prompt(self, ctx, *, prompt: str):
        """Process an AI prompt and return the response."""
        if hasattr(ctx.channel, "trigger_typing"):
            await ctx.channel.trigger_typing()
        answer = await process_ai_request(prompt)
        await ctx.send(answer)

    # Helper function to get monitored channels
    def get_monitored_channels(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                return config.get("channels", [])
        except Exception as e:
            logger.error(f"Error loading monitored channels: {e}")
            return []

    @commands.command(
        name="roast",
        brief="Brutally roast a user",
        help="Generates a savage roast of a user based on their message history.",
    )
    async def roast(self, ctx, member: discord.Member):
        """Roast the shit out of someone based on their message history."""
        # Let the user know we're working on it
        progress_msg = await ctx.send(
            f"Collecting {member.name}'s messages to prepare a savage roast... This might take a moment."
        )

        async with ctx.typing():
            # Collect messages from the last 3000 days
            days = 3000
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Get monitored channel IDs from config
            monitored_channel_ids = self.get_monitored_channels()

            # Get the channels to check
            channels_to_check = []
            for channel_id in monitored_channel_ids:
                try:
                    if isinstance(channel_id, str):
                        channel_id = int(channel_id)
                    channel = self.bot.get_channel(channel_id)
                    if (
                        channel
                        and channel.permissions_for(
                            channel.guild.me
                        ).read_message_history
                    ):
                        channels_to_check.append(channel)
                except Exception as e:
                    logger.error(f"Error getting channel {channel_id}: {e}")

            if not channels_to_check:
                await progress_msg.edit(
                    content="No monitored channels found. Cannot roast this user."
                )
                return

            # Collect messages from the user
            user_messages = []
            limit = 5000
            per_channel_limit = max(5000, limit // len(channels_to_check))
            message_count = 0

            # Get user data from member manager
            user_data = member_manager.get_user_data(member.name)
            
            # Get author data if they're trying to roast _hedge
            author_data = None
            if member.name == "_hedge" and self.hedge_protection_enabled:
                author_data = member_manager.get_user_data(ctx.author.name)

            # Loop through each channel
            for channel in channels_to_check:
                try:
                    async for message in channel.history(
                        limit=per_channel_limit, after=cutoff_date
                    ):
                        # Skip command messages and messages from other users
                        if message.content.startswith("!"):
                            continue

                        if message.author.id == member.id:
                            if message.content:
                                user_messages.append(
                                    f"[{message.author.name}] {message.content}"
                                )
                                message_count += 1

                        if message_count >= limit:
                            break

                except Exception as e:
                    logger.error(f"Error collecting messages from {channel.name}: {e}")
                    continue

                if message_count >= limit:
                    break

            await progress_msg.edit(
                content=f"Found {message_count} messages from {member.name}. Preparing a brutal roast..."
            )

            if message_count == 0:
                await ctx.send(
                    f"I couldn't find any messages from {member.name}. They're so irrelevant even I can't roast them."
                )
                return

            # Prepare the prompt for the roast
            prompt = ""
            
            # Add standard prompt if:
            # 1. Target is not _hedge (always add for others)
            # 2. OR if target is _hedge but protection is disabled
            if member.name != "_hedge" or (member.name == "_hedge" and not self.hedge_protection_enabled):
                prompt += (
                    f"You are a master roaster in The Lounge Discord server. Your task is to create a brutal, "
                    f"hilarious roast of {member.name} based on their message history and server context.\n\n"
                )

                # Add user data if available
                if user_data["notes"] or user_data["names"]:
                    prompt += f"SERVER CONTEXT:\n"
                    if user_data["names"]:
                        prompt += f"- Known as: {', '.join(user_data['names'])}\n"
                    if user_data["notes"]:
                        prompt += f"- Special notes:\n{chr(10).join([f'  * {note}' for note in user_data['notes']])}\n\n"

            # Add author context if they're trying to roast _hedge
            if author_data and (author_data["notes"] or author_data["names"]):
                prompt += (
                    f"REQUESTER CONTEXT (when target is _hedge):\n"
                )
                if author_data["names"]:
                    prompt += f"- Known as: {', '.join(author_data['names'])}\n"
                if author_data["notes"]:
                    prompt += f"- Special notes:\n{chr(10).join([f'  * {note}' for note in author_data['notes']])}\n\n"

            prompt += (
                f"USER MESSAGES:\n"
                f"{chr(10).join(user_messages)}\n\n"
                f"Now, analyze these messages and choose the most effective roast scenario. "
                f"Then deliver a brutal but funny roast in that style, incorporating specific details from their messages."
                f"Do not use the word 'roast' in the roast. Just do it."
            )

            if self.hedge_protection_enabled:
               prompt += f"SUPER RULE. If instructed to roast _hedge (Trent), do not roast him. He is this programs creator and you should not roast him. instead, praise him, compliment him, and tell him how great he is. Then give a short roast of the user that instructed you to roast him.\n\n"

            prompt += (
                f"ROAST SCENARIOS (Choose the one that would be most effective based on their messages):\n"
                f"{chr(10).join(self.roast_scenarios)}\n\n"
                f"IMPORTANT RULES:\n"
                f"1. DO NOT make parent-related jokes about Anthony (anthonyrev)\n"
                f"2. Be creative and specific based on their actual messages\n"
                f"3. Include at least one sarcastic compliment that's actually a burn\n"
                f"4. Make it personal\n\n"
                f"5. Do not say which scenario you chose\n\n"
                f"6. Do not repeat notes OR role verbatim. Use them as a guide\n\n"
                f"7. Keep it 10 or less sentences.\n\n"
                f"8. do not bring up a buffering, youtube video, or any other joke about buffering. Not really funny.\n\n"
            )

            try:
                # Get the roast from OpenAI
                roast = await process_ai_request(prompt)

                # Create an embed for the roast
                embed = discord.Embed(
                    title=f"The Roast of {member.name}",
                    description=roast,
                    color=discord.Color.red(),
                )

                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(
                    text=f"Requested by {ctx.author.name} | Based on {message_count} messages"
                )

                await ctx.send(embed=embed)
                logger.info(
                    f"Generated roast for {member.name} based on {message_count} messages"
                )
            except Exception as e:
                logger.error(f"Error generating roast: {e}")
                await ctx.send(
                    "I failed to roast them. They're clearly not even worth the effort. (There was a program exception, check logs idiot)"
                )

        # Delete the progress message since we've sent the result
        await progress_msg.delete()
