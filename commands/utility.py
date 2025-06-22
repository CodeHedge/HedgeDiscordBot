from discord.ext import commands
import discord
from datetime import datetime, timezone
import time
import logging
import asyncio
from config import load_config

logger = logging.getLogger(__name__)

class UtilityCommands(commands.Cog):
    """Utility commands for server and user information"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()
        self.sudo_users = self.config.get('sudo', [])
        logger.info("UtilityCommands cog initialized")

    def is_sudo(self):
        """Check if user is a sudo user"""
        async def predicate(ctx):
            return ctx.author.id in self.sudo_users
        return commands.check(predicate)

    @commands.command(
        name="serverinfo",
        brief="Display server statistics",
        help="Shows detailed information about the current Discord server, including member count, channel counts, and server age."
    )
    async def serverinfo(self, ctx):
        """Display server statistics and information."""
        guild = ctx.guild
        
        # Skip if this is a DM
        if not guild:
            await ctx.send("This command can only be used in a server.")
            return
            
        # Get creation time and format it
        creation_time = guild.created_at.strftime("%B %d, %Y")
        
        # Handle timezone aware datetime properly
        now = datetime.now(timezone.utc)
        time_since = (now - guild.created_at).days
        
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
        
    @commands.command(
        name="userinfo",
        brief="Show user details",
        help="Displays detailed information about a user, including join date, roles, and status."
    )
    async def userinfo(self, ctx, member: discord.Member = None):
        """Show detailed information about a user."""
        # If no member is specified, use the command invoker
        if member is None:
            member = ctx.author
            
        # Get join time and format it
        joined_time = member.joined_at.strftime("%B %d, %Y") if member.joined_at else "Unknown"
        
        # Handle timezone aware datetime properly
        now = datetime.now(timezone.utc)
        time_since_join = (now - member.joined_at).days if member.joined_at else 0
        time_since_creation = (now - member.created_at).days
        
        # Get account creation time
        creation_time = member.created_at.strftime("%B %d, %Y")
        
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

    @commands.command(
        name="send_invites",
        brief="Send invites to all servers (Sudo only)",
        help="Sends the sudo user invites to every server the bot is in. Only available to sudo users."
    )
    async def send_invites(self, ctx):
        """Send invites to all servers the bot is in to sudo users."""
        if ctx.author.id not in self.sudo_users:
            await ctx.send("You do not have permission to use this command.")
            return
            
        # Can only be used by sudo users
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return
            
        invites_sent = 0
        failed_invites = []
        
        # Get the sudo user
        sudo_user = ctx.author
        
        for guild in self.bot.guilds:
            try:
                # Skip if the user is already in the guild
                if guild.get_member(sudo_user.id):
                    continue
                    
                # Try to create an invite
                invite = None
                
                # Try to get the system channel first
                if guild.system_channel and guild.system_channel.permissions_for(guild.me).create_instant_invite:
                    invite = await guild.system_channel.create_invite(max_age=86400, max_uses=1, reason="Sudo user invite")
                else:
                    # Find any text channel we can create an invite in
                    for channel in guild.text_channels:
                        if channel.permissions_for(guild.me).create_instant_invite:
                            invite = await channel.create_invite(max_age=86400, max_uses=1, reason="Sudo user invite")
                            break
                
                if invite:
                    # Send the invite via DM
                    try:
                        embed = discord.Embed(
                            title=f"Server Invite: {guild.name}",
                            description=f"You've been invited to join **{guild.name}**",
                            color=discord.Color.blue()
                        )
                        embed.add_field(name="Invite Link", value=str(invite), inline=False)
                        embed.add_field(name="Members", value=guild.member_count, inline=True)
                        embed.add_field(name="Expires", value="24 hours", inline=True)
                        
                        if guild.icon:
                            embed.set_thumbnail(url=guild.icon.url)
                            
                        await sudo_user.send(embed=embed)
                        invites_sent += 1
                    except discord.Forbidden:
                        failed_invites.append(f"{guild.name} (couldn't DM)")
                else:
                    failed_invites.append(f"{guild.name} (no invite permissions)")
                    
            except Exception as e:
                failed_invites.append(f"{guild.name} (error: {str(e)})")
        
        # Send summary
        embed = discord.Embed(
            title="Invite Summary",
            color=discord.Color.green() if invites_sent > 0 else discord.Color.red()
        )
        embed.add_field(name="Invites Sent", value=str(invites_sent), inline=True)
        embed.add_field(name="Failed", value=str(len(failed_invites)), inline=True)
        
        if failed_invites:
            failed_text = "\n".join(failed_invites[:10])  # Limit to 10 to avoid embed limits
            if len(failed_invites) > 10:
                failed_text += f"\n... and {len(failed_invites) - 10} more"
            embed.add_field(name="Failed Invites", value=failed_text, inline=False)
            
        await ctx.send(embed=embed)

    @commands.command(
        name="role_menu",
        brief="Create a role selection menu via DM",
        help="Sends a DM with emoji reactions to select roles. Only shows roles the bot can assign."
    )
    async def role_menu(self, ctx):
        """Create a role selection menu via DM with emoji reactions."""
        if not ctx.guild:
            await ctx.send("This command can only be used in a server.")
            return
            
        guild = ctx.guild
        member = guild.get_member(ctx.author.id)
        
        if not member:
            await ctx.send("Could not find you in this server.")
            return
            
        # Get all roles the bot can assign (below bot's highest role and not @everyone)
        bot_member = guild.get_member(self.bot.user.id)
        bot_top_role = bot_member.top_role
        
        assignable_roles = []
        for role in guild.roles:
            if (role.position < bot_top_role.position and 
                role != guild.default_role and 
                not role.managed and
                not role.is_premium_subscriber()):
                assignable_roles.append(role)
        
        if not assignable_roles:
            await ctx.send("No assignable roles found in this server.")
            return
            
        # Limit to 20 roles to avoid embed limits and emoji limitations
        if len(assignable_roles) > 20:
            assignable_roles = assignable_roles[:20]
            
        # Create emoji mappings (using numbers and letters)
        emoji_list = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟',
                     '🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯']
        
        # Create the embed
        embed = discord.Embed(
            title=f"Role Selection - {guild.name}",
            description="React with the corresponding emoji to toggle roles:",
            color=discord.Color.blue()
        )
        
        role_emoji_map = {}
        role_description = ""
        
        for i, role in enumerate(assignable_roles):
            emoji = emoji_list[i]
            role_emoji_map[emoji] = role
            
            # Check if user already has the role
            has_role = "✅" if role in member.roles else "❌"
            role_description += f"{emoji} {role.name} {has_role}\n"
            
        embed.add_field(name="Available Roles", value=role_description, inline=False)
        embed.add_field(name="Instructions", 
                       value="✅ = You have this role\n❌ = You don't have this role\n\nReact to toggle roles on/off", 
                       inline=False)
        embed.set_footer(text="This menu will expire in 5 minutes")
        
        try:
            # Send the DM
            dm_message = await ctx.author.send(embed=embed)
            
            # Add all the reactions
            for emoji in role_emoji_map.keys():
                await dm_message.add_reaction(emoji)
                
            # Confirm in the original channel
            await ctx.send(f"Role selection menu sent to your DMs! React to the emojis to toggle roles.")
            
            # Wait for reactions
            def check(reaction, user):
                return (user == ctx.author and 
                       str(reaction.emoji) in role_emoji_map and 
                       reaction.message.id == dm_message.id)
            
            timeout_time = 300  # 5 minutes
            start_time = time.time()
            
            while time.time() - start_time < timeout_time:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=30, check=check)
                    
                    # Get the role
                    role = role_emoji_map[str(reaction.emoji)]
                    
                    # Toggle the role
                    if role in member.roles:
                        await member.remove_roles(role, reason="Role menu selection")
                        action = "removed"
                        action_emoji = "➖"
                    else:
                        await member.add_roles(role, reason="Role menu selection")
                        action = "added"
                        action_emoji = "➕"
                    
                    # Send confirmation
                    confirm_embed = discord.Embed(
                        title="Role Updated",
                        description=f"{action_emoji} {action.title()} role **{role.name}**",
                        color=discord.Color.green()
                    )
                    await ctx.author.send(embed=confirm_embed)
                    
                    # Remove the user's reaction
                    await reaction.remove(user)
                    
                except asyncio.TimeoutError:
                    continue
                    
        except discord.Forbidden:
            await ctx.send("I couldn't send you a DM. Please check your privacy settings.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}") 