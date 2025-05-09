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
            await ctx.send(f"Note added for {username}")
        else:
            await ctx.send("Failed to add note")

    @commands.command(name='name')
    async def add_name(self, ctx, username: str, *, name: str):
        """Add a name for a user"""
        if member_manager.add_name(username, name):
            await ctx.send(f"Name '{name}' added for {username}")
        else:
            await ctx.send(f"Name '{name}' already exists for {username}")

    @commands.command(name='getnotes')
    @is_sudo()
    async def get_notes(self, ctx, username: str):
        """Get all notes for a user (Sudo only)"""
        user_data = member_manager.get_user_data(username)
        if user_data["notes"]:
            notes_text = "\n".join([f"{i}. {note}" for i, note in enumerate(user_data["notes"])])
            await ctx.send(f"Notes for {username}:\n{notes_text}")
        else:
            await ctx.send(f"No notes found for {username}")

    @commands.command(name='removenote')
    @is_sudo()
    async def remove_note(self, ctx, username: str, note_index: str):
        """Remove a note for a user by index (Sudo only)"""
        success, removed_note = member_manager.remove_note(username, note_index)
        if success:
            await ctx.send(f"Removed note: {removed_note}")
        else:
            await ctx.send("Failed to remove note. Make sure the index is valid.")

    @commands.command(name='getnames')
    async def get_names(self, ctx, username: str):
        """Get all names for a user"""
        user_data = member_manager.get_user_data(username)
        if user_data["names"]:
            names_text = "\n".join([f"- {name}" for name in user_data["names"]])
            await ctx.send(f"Names for {username}:\n{names_text}")
        else:
            await ctx.send(f"No names found for {username}")

async def setup(bot):
    await bot.add_cog(MemberCommands(bot)) 