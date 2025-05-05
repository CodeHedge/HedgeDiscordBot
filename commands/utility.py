from discord.ext import commands
import discord
from datetime import datetime
import time

class UtilityCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def serverinfo(self, ctx):
        """Display server statistics and information."""
        guild = ctx.guild
        
        # Skip if this is a DM
        if not guild:
            await ctx.send("This command can only be used in a server.")
            return
            
        # Get creation time and format it
        creation_time = guild.created_at.strftime("%B %d, %Y")
        time_since = (datetime.utcnow() - guild.created_at).days
        
        # Count channels by type
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        # Roles info
        role_count = len(guild.roles) - 1  # Subtract @everyone role
        
        # Member info
        total_members = guild.member_count
        online_members = sum(1 for member in guild.members if member.status != discord.Status.offline)
        bot_count = sum(1 for member in guild.members if member.bot)
        
        # Create the embed
        embed = discord.Embed(
            title=f"{guild.name} Server Information",
            description=f"ID: {guild.id}",
            color=discord.Color.blue()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Created On", value=f"{creation_time}\n({time_since} days ago)", inline=True)
        embed.add_field(name="Region", value=str(guild.region) if hasattr(guild, "region") else "N/A", inline=True)
        
        embed.add_field(name="Members", value=f"Total: {total_members}\nOnline: {online_members}\nBots: {bot_count}", inline=True)
        embed.add_field(name="Channels", value=f"Text: {text_channels}\nVoice: {voice_channels}\nCategories: {categories}", inline=True)
        embed.add_field(name="Roles", value=str(role_count), inline=True)
        
        embed.set_footer(text=f"Requested by {ctx.author.name}")
        
        await ctx.send(embed=embed)
        
    @commands.command()
    async def userinfo(self, ctx, member: discord.Member = None):
        """Show detailed information about a user."""
        # If no member is specified, use the command invoker
        if member is None:
            member = ctx.author
            
        # Get join time and format it
        joined_time = member.joined_at.strftime("%B %d, %Y") if member.joined_at else "Unknown"
        time_since_join = (datetime.utcnow() - member.joined_at).days if member.joined_at else 0
        
        # Get account creation time
        creation_time = member.created_at.strftime("%B %d, %Y")
        time_since_creation = (datetime.utcnow() - member.created_at).days
        
        # Get roles (excluding @everyone)
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        roles_str = ", ".join(roles) if roles else "No roles"
        
        # Status and activity
        status = str(member.status).title()
        activity = f"{member.activity.type.name.title()} {member.activity.name}" if member.activity else "None"
        
        # Create the embed
        embed = discord.Embed(
            title=f"{member.name}#{member.discriminator}" if hasattr(member, "discriminator") else member.name,
            description=f"ID: {member.id}",
            color=member.color
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.add_field(name="Joined Server", value=f"{joined_time}\n({time_since_join} days ago)", inline=True)
        embed.add_field(name="Account Created", value=f"{creation_time}\n({time_since_creation} days ago)", inline=True)
        embed.add_field(name="Status", value=status, inline=True)
        
        if member.premium_since:
            boost_time = member.premium_since.strftime("%B %d, %Y")
            embed.add_field(name="Boosting Since", value=boost_time, inline=True)
            
        embed.add_field(name="Activity", value=activity, inline=True)
        
        # Add nickname if they have one
        if member.nick:
            embed.add_field(name="Nickname", value=member.nick, inline=True)
            
        # Add roles in a separate field (may be long)
        embed.add_field(name=f"Roles [{len(roles)}]", value=roles_str, inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author.name}")
        
        await ctx.send(embed=embed) 