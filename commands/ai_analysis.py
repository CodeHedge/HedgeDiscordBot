from discord.ext import commands
import discord
import asyncio
from collections import Counter
import re
from datetime import datetime, timedelta
import logging
from ai import process_ai_request
import json

logger = logging.getLogger(__name__)

class AIAnalysisCommands(commands.Cog):
    """Commands for AI-powered conversation analysis"""
    
    def __init__(self, bot):
        self.bot = bot
        logger.info("AIAnalysisCommands cog initialized")
        
    @commands.command(
        name="summarize",
        brief="Summarize recent messages",
        help="Uses AI to create a concise summary of recent conversation in the current channel."
    )
    async def summarize(self, ctx, limit: int = 25):
        """Summarize recent conversation in the channel."""
        # Limit the number of messages to fetch (to prevent abuse)
        if limit > 100:
            await ctx.send("Maximum summary length is 100 messages.")
            limit = 100
            
        async with ctx.typing():
            # Collect the messages
            messages = []
            async for message in ctx.channel.history(limit=limit):
                if not message.content or message.author.bot:
                    continue
                    
                # Format the message for the prompt
                messages.append(f"{message.author.name}: {message.content}")
                
            if not messages:
                await ctx.send("No messages to summarize.")
                return
                
            # Reverse the messages to get chronological order
            messages.reverse()
            
            # Prepare the prompt for the AI
            prompt = (
                "Please provide a brief but comprehensive summary of the following conversation. "
                "Focus on the main topics discussed, key points made, and any conclusions reached. "
                "Keep the summary concise (3-5 sentences).\n\n"
                f"CONVERSATION (most recent {len(messages)} messages):\n\n"
                + "\n".join(messages)
            )
            
            # Get the summary from OpenAI
            try:
                summary = await process_ai_request(prompt)
                
                # Create an embed for the summary
                embed = discord.Embed(
                    title=f"Channel Summary ({len(messages)} messages)",
                    description=summary,
                    color=discord.Color.blue()
                )
                embed.set_footer(text=f"Requested by {ctx.author.name}")
                
                await ctx.send(embed=embed)
                logger.info(f"Generated summary for {len(messages)} messages in {ctx.channel.name}")
            except Exception as e:
                logger.error(f"Error generating summary: {e}")
                await ctx.send("Sorry, I encountered an error while generating the summary.")
    
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
        name="analyze",
        brief="Analyze user's messages",
        help="Analyzes this user's messaging patterns, word usage, and communication style."
    )
    async def analyze(self, ctx, member: discord.Member = None, days: int = 7, limit: int = 1000):
        """Analyze a user's message patterns and tone."""
        # If in DMs, member must be specified
        if not ctx.guild and not member:
            await ctx.send("When using this command in DMs, you must specify a user to analyze.")
            return
            
        if member is None:
            member = ctx.author
            
        # Limit the days and message count to prevent abuse
        if days > 365:
            await ctx.send("Maximum analysis period is 30 days.")
            days = 365
            
        if limit > 500:
            await ctx.send("Maximum message count is 2000.")
            limit = 500
            
        # Inform the user this might take a while
        progress_msg = await ctx.send(f"Analyzing {member.name}'s messages from the past {days} days... This may take a moment.")
        
        async with ctx.typing():
            # Calculate the cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Collect the messages
            user_messages = []
            message_length = []
            channel_distribution = Counter()
            hour_distribution = Counter()
            word_count = Counter()
            
            # Track some message counts
            message_count = 0
            total_words = 0
            total_chars = 0
            
            checked_messages = 0
            
            # Pattern to extract words
            word_pattern = re.compile(r'\b[a-zA-Z]+\b')
            
            # Get monitored channel IDs from config
            monitored_channel_ids = self.get_monitored_channels()
            
            # Get the channels to check based on monitored channel IDs
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
            
            # If no monitored channels are found, inform the user
            if not channels_to_check:
                await progress_msg.edit(content="No monitored channels found. Cannot analyze messages.")
                return
                
            # Distribute the message limit across channels
            per_channel_limit = max(100, limit // max(1, len(channels_to_check)))
            
            # Update progress message to show start of analysis
            await progress_msg.edit(content=f"Analyzing {member.name}'s messages across {len(channels_to_check)} monitored channels...")
            
            # Loop through each channel
            for channel in channels_to_check:
                try:
                    async for message in channel.history(limit=per_channel_limit, after=cutoff_date):
                        checked_messages += 1
                        
                        if message.author.id != member.id or not message.content:
                            continue
                            
                        # Add to analysis
                        user_messages.append(message.content)
                        message_length.append(len(message.content))
                        
                        # Always use the channel name (monitored channels are always text channels in servers)
                        channel_distribution[channel.name] += 1
                        
                        hour_distribution[message.created_at.hour] += 1
                        
                        # Extract and count words
                        words = word_pattern.findall(message.content.lower())
                        for word in words:
                            if len(word) > 2:  # Skip very short words
                                word_count[word] += 1
                                
                        total_words += len(words)
                        total_chars += len(message.content)
                        message_count += 1
                        
                        # Update progress message periodically
                        if checked_messages % 200 == 0:
                            await progress_msg.edit(content=f"Analyzing {member.name}'s messages... Checked {checked_messages} messages so far.")
                            
                        # If we've hit our overall limit, stop
                        if message_count >= limit:
                            break
                            
                except Exception as e:
                    logger.error(f"Error analyzing channel {channel.name}: {e}")
                    continue
                    
                # If we've hit our overall limit, stop checking more channels
                if message_count >= limit:
                    break
            
            await progress_msg.edit(content=f"Found {message_count} messages from {member.name}. Generating analysis...")
            
            if message_count == 0:
                await ctx.send(f"No messages found from {member.name} in the past {days} days.")
                return
                
            # Calculate some metrics
            avg_length = sum(message_length) / len(message_length) if message_length else 0
            most_active_hour = max(hour_distribution.items(), key=lambda x: x[1])[0] if hour_distribution else "N/A"
            
            # Get the most active channel safely
            most_active_channel = "N/A"
            if channel_distribution:
                most_active_channel = max(channel_distribution.items(), key=lambda x: x[1])[0]
                
            most_common_words = [word for word, count in word_count.most_common(10)]
            
            # Get a sample of messages for AI analysis (limit to avoid exceeding token limits)
            message_sample = user_messages[-50:] if len(user_messages) > 50 else user_messages
            
            # Prepare the prompt for AI analysis
            prompt = (
                f"Analyze the following message sample from a Discord user named {member.name}. "
                "Provide a short analysis of their communication style, apparent personality traits based on their writing, "
                "and the sentiment/tone of their messages. "
                "Keep the analysis professional, respectful, and around 3-4 sentences long.\n\n"
                "MESSAGE SAMPLE:\n\n" + "\n".join(message_sample)
            )
            
            try:
                # Get AI analysis
                ai_analysis = await process_ai_request(prompt)
                
                # Create an embed with the analysis
                embed = discord.Embed(
                    title=f"Analysis for {member.name}",
                    description=ai_analysis,
                    color=member.color
                )
                
                embed.set_thumbnail(url=member.display_avatar.url)
                
                # Add statistical data
                embed.add_field(
                    name="Activity Statistics", 
                    value=f"**Messages:** {message_count}\n"
                          f"**Average length:** {avg_length:.1f} characters\n"
                          f"**Words per message:** {total_words/message_count:.1f}\n"
                          f"**Most active hour:** {most_active_hour}:00\n",
                    inline=True
                )
                
                embed.add_field(
                    name="Word Usage",
                    value=f"**Total words:** {total_words}\n"
                          f"**Unique words:** {len(word_count)}\n"
                          f"**Common words:** {', '.join(most_common_words[:5])}",
                    inline=True
                )
                
                # Add channel distribution if in a guild
                if ctx.guild and len(channel_distribution) > 0:
                    top_channels = sorted(channel_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
                    channel_stats = "\n".join([f"**#{ch}:** {count} msgs" for ch, count in top_channels])
                    embed.add_field(
                        name="Top Channels",
                        value=channel_stats,
                        inline=False
                    )
                
                embed.set_footer(text=f"Analysis based on {message_count} messages from the past {days} days")
                
                await ctx.send(embed=embed)
                logger.info(f"Generated analysis for {member.name} based on {message_count} messages")
            except Exception as e:
                logger.error(f"Error generating analysis: {e}")
                await ctx.send("Sorry, I encountered an error while generating the analysis.") 