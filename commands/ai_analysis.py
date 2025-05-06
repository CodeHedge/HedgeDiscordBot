from discord.ext import commands
import discord
import asyncio
from collections import Counter
import re
from datetime import datetime, timedelta
import logging
from ai import process_ai_request
import json
from config import get_analyze_limits

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
            
        # Get limits from configuration
        max_days, max_messages = get_analyze_limits()
        
        # Limit the days and message count based on configuration
        if days > max_days:
            await ctx.send(f"Maximum analysis period is {max_days} days.")
            days = max_days
            
        if limit > max_messages:
            await ctx.send(f"Maximum message count is {max_messages}.")
            limit = max_messages
            
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
            
            # Pattern to extract words - only actual words, not URLs or domains
            word_pattern = re.compile(r'\b[a-zA-Z]+\b')
            
            # Words to exclude from the common words list (web/URL related)
            excluded_words = set([
                'http', 'https', 'www', 'com', 'net', 'org', 'gif', 'jpg', 'png',
                'tenor', 'view', 'discord', 'youtube', 'twitter', 'twitch', 'imgur',
                'gfycat', 'streamable', 'reddit', 'image', 'video', 'html', 'and','the',
                'is','in','at','to','of','is','a','for','by','this','that','it','with',
                'as','was','will','can','could','may','might','must','should','would',
                'shall','do','does','did','done','been','being'
            ])
            
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
                            if len(word) > 2 and word not in excluded_words:  # Skip very short words and excluded words
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
                
            # Get meaningful common words (filtered)
            most_common_words = []
            for word, count in word_count.most_common(15):  # Get more words to ensure we have enough after filtering
                if word not in excluded_words and len(most_common_words) < 5:
                    most_common_words.append(word)
            
            # If we don't have enough words after filtering, add a message
            if not most_common_words:
                most_common_words = ["No significant words found"]
                
            # Get a sample of messages for AI analysis (limit to avoid exceeding token limits)
            message_sample = user_messages[-50:] if len(user_messages) > 50 else user_messages
            
            # Calculate % of messages with links/media
            media_pattern = re.compile(r'https?://\S+|www\.\S+|\.(gif|jpg|png|mp4|webm)\b', re.IGNORECASE)
            emoji_pattern = re.compile(r'<a?:\w+:\d+>|:\w+:|[\U0001F000-\U0001F9FF]|[\u2600-\u26FF]|[\u2700-\u27BF]')
            
            media_count = sum(1 for msg in user_messages if media_pattern.search(msg))
            emoji_count = sum(1 for msg in user_messages if emoji_pattern.search(msg))
            
            media_percent = (media_count / message_count) * 100 if message_count > 0 else 0
            emoji_percent = (emoji_count / message_count) * 100 if message_count > 0 else 0
            
            # Prepare the prompt for AI analysis with more specific instructions
            prompt = (
                f"Analyze the following message sample from a Discord user named {member.name}. "
                "Your goal is to provide a unique, insightful analysis that captures what sets this user apart from others. "
                "Consider these aspects:\n"
                "1. Communication style: How do they structure messages? Are they verbose or concise? Formal or casual?\n"
                "2. Topics: What specific subjects do they discuss most? Any unique interests?\n"
                "3. Personality indicators: What traits are evident in their writing style?\n"
                "4. Tone: What emotions or attitudes come through in their messages?\n"
                "5. Distinctiveness: What makes their style unique compared to other users?\n\n"
                f"Additional context: About {media_percent:.1f}% of their messages contain links/media, and {emoji_percent:.1f}% use emojis.\n\n"
                "Provide a detailed, specific analysis in 3-4 sentences that highlights what makes this user's communication unique. "
                "Focus on concrete examples rather than generalities. Be respectful but insightful.\n\n"
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
                          f"**Common words:** {', '.join(most_common_words)}",
                    inline=True
                )
                
                # Add media usage statistics
                embed.add_field(
                    name="Content Style",
                    value=f"**Uses media/links:** {media_percent:.1f}%\n"
                          f"**Uses emojis:** {emoji_percent:.1f}%",
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