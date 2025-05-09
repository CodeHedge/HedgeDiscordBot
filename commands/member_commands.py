import discord
from discord.ext import commands
from config import member_manager, load_config

class MemberCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()
        self.sudo_users = self.config.get('sudo', [])

    def is_sudo():
        async def predicate(ctx):
            return ctx.author.id in ctx.cog.sudo_users
        return commands.check(predicate)

    @commands.command(name='note')
    async def add_note(self, ctx, username: str, *, note: str):
        """Add a note for a user"""
        if member_manager.add_note(username, note):
            embed = discord.Embed(
                title="Note Added",
                description=f"Note added for {username}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Error",
                description="Failed to add note",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name='name')
    @is_sudo()
    async def add_name(self, ctx, username: str, *, name: str):
        """Add a name for a user (Sudo only)"""
        if member_manager.add_name(username, name):
            embed = discord.Embed(
                title="Name Added",
                description=f"Name '{name}' added for {username}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Name Already Exists",
                description=f"Name '{name}' already exists for {username}",
                color=discord.Color.yellow()
            )
            await ctx.send(embed=embed)

    @commands.command(name='alias')
    @is_sudo()
    async def add_alias(self, ctx, username: str, *, alias: str):
        """Add an alias for a user (Sudo only)"""
        if member_manager.add_alias(username, alias):
            embed = discord.Embed(
                title="Alias Added",
                description=f"Alias '{alias}' added for {username}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Alias Already Exists",
                description=f"Alias '{alias}' already exists for {username}",
                color=discord.Color.yellow()
            )
            await ctx.send(embed=embed)

    @commands.command(name='getnotes')
    @is_sudo()
    async def get_notes(self, ctx, username: str):
        """Get all notes for a user (Sudo only)"""
        user_data = member_manager.get_user_data(username)
        
        # Try to find the user in the guild
        user = None
        for guild in self.bot.guilds:
            user = discord.utils.get(guild.members, name=username)
            if user:
                break

        embed = discord.Embed(
            title=f"Notes for {username}",
            color=discord.Color.blue()
        )

        if user and user.avatar:
            embed.set_thumbnail(url=user.avatar.url)

        if user_data["notes"]:
            notes_text = "\n".join([f"{i+1}. {note}" for i, note in enumerate(user_data["notes"])])
            embed.description = notes_text
            embed.set_footer(text="Use !removenote <username> <number> to remove a note")
        else:
            embed.description = f"No notes found for {username}"

        await ctx.send(embed=embed)

    @commands.command(name='removenote')
    @is_sudo()
    async def remove_note(self, ctx, username: str, note_index: str):
        """Remove a note for a user by index (Sudo only)"""
        try:
            # Convert to 0-based index
            note_index = int(note_index) - 1
            if note_index < 0:
                raise ValueError("Index must be positive")
                
            success, removed_note = member_manager.remove_note(username, str(note_index))
            
            embed = discord.Embed(
                title="Note Removed" if success else "Error",
                description=f"Removed note: {removed_note}" if success else "Failed to remove note. Make sure the index is valid.",
                color=discord.Color.green() if success else discord.Color.red()
            )
            await ctx.send(embed=embed)
        except ValueError:
            embed = discord.Embed(
                title="Error",
                description="Please provide a valid positive number for the note index",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command(name='getnames')
    async def get_names(self, ctx, username: str):
        """Get all names for a user"""
        user_data = member_manager.get_user_data(username)
        
        # Try to find the user in the guild
        user = None
        for guild in self.bot.guilds:
            user = discord.utils.get(guild.members, name=username)
            if user:
                break

        embed = discord.Embed(
            title=f"Names for {username}",
            color=discord.Color.blue()
        )

        if user and user.avatar:
            embed.set_thumbnail(url=user.avatar.url)

        if user_data["names"]:
            names_text = "\n".join([f"- {name}" for name in user_data["names"]])
            embed.description = names_text
        else:
            embed.description = f"No names found for {username}"

        await ctx.send(embed=embed)

    @commands.command(name='getaliases')
    @is_sudo()
    async def get_aliases(self, ctx, username: str):
        """Get all aliases for a user (Sudo only)"""
        aliases = member_manager.get_user_aliases(username)
        
        # Create an embed for the response
        embed = discord.Embed(
            title=f"Aliases for {username}",
            color=discord.Color.blue()
        )
        
        if aliases:
            embed.description = "\n".join([f"• {alias}" for alias in aliases])
        else:
            embed.description = "No aliases found for this user."
            
        # Try to find the user in any guild to get their profile picture
        for guild in self.bot.guilds:
            member = guild.get_member_named(username)
            if member:
                embed.set_thumbnail(url=member.display_avatar.url)
                break
                
        await ctx.send(embed=embed)

    @commands.command(name='deleteuser')
    @is_sudo()
    async def delete_user(self, ctx, username: str):
        """Delete a user and all their data from members.json (Sudo only)"""
        success, deleted_data = member_manager.delete_user(username)
        
        # Create an embed for the response
        if success:
            embed = discord.Embed(
                title="User Deleted",
                description=f"Successfully deleted all data for {username}",
                color=discord.Color.green()
            )
            
            # Add details about what was deleted
            if deleted_data:
                details = []
                if deleted_data.get("notes"):
                    details.append(f"• {len(deleted_data['notes'])} notes")
                if deleted_data.get("names"):
                    details.append(f"• {len(deleted_data['names'])} names")
                if deleted_data.get("aliases"):
                    details.append(f"• {len(deleted_data['aliases'])} aliases")
                
                if details:
                    embed.add_field(
                        name="Deleted Data",
                        value="\n".join(details),
                        inline=False
                    )
        else:
            embed = discord.Embed(
                title="Error",
                description=f"Could not find user {username} in the database",
                color=discord.Color.red()
            )
            
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MemberCommands(bot)) 