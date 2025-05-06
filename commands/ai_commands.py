from discord.ext import commands
import discord
from ai import process_ai_request
import json
import logging
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class AICommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("AICommands cog initialized")

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
            with open('config.json', 'r') as f:
                config = json.load(f)
                return config.get('channels', [])
        except Exception as e:
            logger.error(f"Error loading monitored channels: {e}")
            return []
            
    @commands.command(
        name="roast",
        brief="Brutally roast a user",
        help="Generates a savage roast of a user based on their message history."
    )
    async def roast(self, ctx, member: discord.Member):
        """Roast the shit out of someone based on their message history."""
        # Let the user know we're working on it
        progress_msg = await ctx.send(f"Collecting {member.name}'s messages to prepare a savage roast... This might take a moment.")
        
        async with ctx.typing():
            # Collect messages from the last 30 days
            days = 30
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get monitored channel IDs from config
            monitored_channel_ids = self.get_monitored_channels()
            
            # Get the channels to check
            channels_to_check = []
            for channel_id in monitored_channel_ids:
                try:
                    # Convert channel ID to integer if it's a string
                    if isinstance(channel_id, str):
                        channel_id = int(channel_id)
                        
                    channel = self.bot.get_channel(channel_id)
                    if channel and channel.permissions_for(channel.guild.me).read_message_history:
                        channels_to_check.append(channel)
                except Exception as e:
                    logger.error(f"Error getting channel {channel_id}: {e}")
            
            if not channels_to_check:
                await progress_msg.edit(content="No monitored channels found. Cannot roast this user.")
                return
                
            # Collect up to 100 messages from the user
            user_messages = []
            limit = 5000
            per_channel_limit = max(50, limit // len(channels_to_check))
            message_count = 0
            
            # Keep track of some patterns for better roasting
            url_pattern = re.compile(r'https?://\S+')
            emoji_pattern = re.compile(r'<a?:\w+:\d+>|:\w+:|[\U0001F000-\U0001F9FF]|[\u2600-\u26FF]|[\u2700-\u27BF]')
            
            emoji_count = 0
            url_count = 0
            caps_count = 0
            exclamation_count = 0
            question_count = 0
            word_count = 0
            
            # Loop through each channel
            for channel in channels_to_check:
                try:
                    async for message in channel.history(limit=per_channel_limit, after=cutoff_date):
                        if message.author.id != member.id or not message.content:
                            continue
                            
                        # Add to collection
                        user_messages.append(message.content)
                        message_count += 1
                        
                        # Count patterns
                        if url_pattern.search(message.content):
                            url_count += 1
                        
                        emoji_count += len(emoji_pattern.findall(message.content))
                        
                        if message.content.isupper() and len(message.content) > 5:
                            caps_count += 1
                            
                        exclamation_count += message.content.count('!')
                        question_count += message.content.count('?')
                        word_count += len(message.content.split())
                        
                        if message_count >= limit:
                            break
                            
                except Exception as e:
                    logger.error(f"Error collecting messages from {channel.name}: {e}")
                    continue
                    
                if message_count >= limit:
                    break
                    
            await progress_msg.edit(content=f"Found {message_count} messages from {member.name}. Preparing a brutal roast...")
            
            if message_count == 0:
                await ctx.send(f"I couldn't find any messages from {member.name}. They're so irrelevant even I can't roast them.")
                return
                
            # Prepare stats for roasting
            stats = {
                "message_count": message_count,
                "avg_length": word_count / message_count if message_count > 0 else 0,
                "emoji_rate": emoji_count / message_count if message_count > 0 else 0,
                "url_rate": url_count / message_count if message_count > 0 else 0,
                "caps_rate": caps_count / message_count if message_count > 0 else 0,
                "exclamation_rate": exclamation_count / message_count if message_count > 0 else 0,
                "question_rate": question_count / message_count if message_count > 0 else 0,
            }
            
            # Get a sample of messages
            message_sample = user_messages[-50:] if len(user_messages) > 50 else user_messages
            
            # Prepare the prompt for the roast
            prompt = (
                f"Roast the absolute shit out of this Discord user based on their message history. Be BRUTAL, savage, and hilarious.\n\n"
                f"User: {member.name}\n"
                f"Basic stats:\n"
                f"- Sends about {stats['avg_length']:.1f} words per message\n"
                f"- Uses emojis {stats['emoji_rate']:.2f} times per message\n"
                f"- Posts links {stats['url_rate']:.2f} times per message\n"
                f"- Types in ALL CAPS {stats['caps_rate']:.2f} times per message\n"
                f"- Uses exclamation points {stats['exclamation_rate']:.2f} times per message\n"
                f"- Asks questions {stats['question_rate']:.2f} times per message\n\n"
                f"Create a hilarious, ruthless roast that would make a comedian proud. Don't hold back AT ALL. "
                f"Focus on their writing style, interests, and quirks visible in these messages. "
                f"Be creative, specific, and HARSH. Make it personal based on their actual messages. "
                f"Include at least one sarcastic compliment that's actually a burn. Keep it to a short paragraph.\n\n"
                f"SAMPLE MESSAGES:\n\n" + "\n".join(message_sample)
            )
            
            try:
                # Get the roast from OpenAI
                roast = await process_ai_request(prompt)
                
                # Create an embed for the roast
                embed = discord.Embed(
                    title=f"Brutal Roast of {member.name}",
                    description=roast,
                    color=discord.Color.red()
                )
                
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"Requested by {ctx.author.name} | Based on {message_count} messages")
                
                await ctx.send(embed=embed)
                logger.info(f"Generated roast for {member.name} based on {message_count} messages")
            except Exception as e:
                logger.error(f"Error generating roast: {e}")
                await ctx.send("I failed to roast them. They're clearly not even worth the effort.")
        
        # Delete the progress message since we've sent the result
        await progress_msg.delete() 