import os
import discord
from discord.ext import commands
from datetime import datetime
from discord import app_commands

# --- Constants ---
LOG_CHANNEL_ID = 1275464228421107713

# --- Helper Functions ---

def format_dt(dt):
    """Formats a datetime object into a standard string."""
    return dt.strftime("%m/%d/%Y %I:%M %p")

async def send_log(guild: discord.Guild, embed: discord.Embed):
    """Sends an embed to the designated log channel."""
    log_channel = guild.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            print(f"Missing permissions to send log in guild: {guild.id}")
        except discord.HTTPException as e:
            print(f"Failed to send log: {e}")

# --- Cog Class ---

class Rancour(commands.Cog):
    """
    Handles all logging for server events (joins, leaves, edits, etc.)
    and provides moderation-related commands.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Rancour has been loaded and is ready.")

    # Role Added/Removed + Nickname Changed
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Check for added roles
        added_roles = [r for r in after.roles if r not in before.roles]
        for role in added_roles:
            embed = discord.Embed(
                title=":white_check_mark: Role Added to User",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="User", value=f"{after} | {after.id}", inline=False)
            embed.add_field(name="Role", value=role.mention, inline=False)
            await send_log(after.guild, embed)

        # Check for removed roles
        removed_roles = [r for r in before.roles if r not in after.roles]
        for role in removed_roles:
            embed = discord.Embed(
                title=":x: Role Removed from User",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="User", value=f"{after} | {after.id}", inline=False)
            embed.add_field(name="Role", value=role.mention, inline=False)
            await send_log(after.guild, embed)

        # Check for nickname change
        if before.nick != after.nick:
            embed = discord.Embed(
                title=":pencil: Nickname Changed",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="User", value=f"{after} | {after.id}", inline=False)
            embed.add_field(name="Old Nickname", value=before.nick or "*None*", inline=True)
            embed.add_field(name="New Nickname", value=after.nick or "*None*", inline=True)
            await send_log(after.guild, embed)

    # Message Edited
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot:
            return
        if before.content == after.content:
            return
        if not before.guild: # Ignore DMs
            return

        embed = discord.Embed(
            title=":pencil: Message Updated",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Old Message", value=before.content or "*no content*", inline=False)
        embed.add_field(name="New Message", value=after.content or "*no content*", inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=True)
        embed.add_field(name="Author", value=f"{before.author} | {before.author.id}", inline=True)
        await send_log(before.guild, embed)

    # Message Deleted
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return
        if not message.guild: # Ignore DMs
            return

        embed = discord.Embed(
            title=":wastebasket: Message Deleted",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Deleted Message", value=message.content or "*no content*", inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(name="Author", value=f"{message.author} | {message.author.id}", inline=True)
        await send_log(message.guild, embed)

    # Channel Created
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        embed = discord.Embed(
            title=":new: Channel Created",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Channel", value=channel.mention, inline=False)
        embed.add_field(name="Channel Name", value=channel.name, inline=True)
        embed.add_field(name="Channel ID", value=channel.id, inline=True)
        embed.add_field(name="Channel Type", value=channel.type, inline=True)
        await send_log(channel.guild, embed)

    # Channel Deleted
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        embed = discord.Embed(
            title=":regional_indicator_x: Channel Deleted",
            color=discord.Color.darker_grey(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Channel Name", value=channel.name, inline=True)
        embed.add_field(name="Channel ID", value=channel.id, inline=True)
        embed.add_field(name="Channel Type", value=channel.type, inline=True)
        await send_log(channel.guild, embed)

    # Channel Updated
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        embed = discord.Embed(
            title=":gear: Channel Updated",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Channel", value=after.mention, inline=False)
        
        if before.name != after.name:
            embed.add_field(name="Old Channel Name", value=before.name, inline=True)
            embed.add_field(name="Updated Channel Name", value=after.name, inline=True)
        
        # Add more checks here if you want to log other updates (e.g., permissions, topic)
        # For this conversion, we'll keep it as it was (only name)
        
        if len(embed.fields) > 1: # Only send if something changed
            await send_log(after.guild, embed)

    # Member Joined
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        embed = discord.Embed(
            title=":wave: Member Joined",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="User", value=f"{member} | {member.id}", inline=False)
        embed.add_field(name="Account Created", value=format_dt(member.created_at), inline=False)
        await send_log(member.guild, embed)

    # Member Left / Kicked
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        entry = None

        # Try to find a kick log
        try:
            async for log in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
                if log.target.id == member.id and (datetime.utcnow() - log.created_at).total_seconds() < 5:
                    entry = log
                    break
        except discord.Forbidden:
            print(f"Missing audit log permissions in guild: {guild.id}")

        embed = discord.Embed(timestamp=datetime.utcnow())
        embed.add_field(name="User", value=f"{member} | {member.id}", inline=False)

        if entry:
            embed.title = ":anger: Member Kicked"
            embed.color = discord.Color.dark_red()
            embed.add_field(name="By", value=f"{entry.user} | {entry.user.id}", inline=False)
            embed.add_field(name="Reason", value=entry.reason or "*No reason provided*", inline=False)
        else:
            embed.title = ":saluting_face: Member Left"
            embed.color = discord.Color.red()

        await send_log(guild, embed)

    # Member Banned
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        entry = None

        # Try to find a ban log
        try:
            async for log in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if log.target.id == user.id and (datetime.utcnow() - log.created_at).total_seconds() < 5:
                    entry = log
                    break
        except discord.Forbidden:
            print(f"Missing audit log permissions in guild: {guild.id}")

        embed = discord.Embed(
            title=":boxing_glove: Member Banned",
            color=discord.Color.dark_red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="User", value=f"{user} | {user.id}", inline=False)

        if entry:
            embed.add_field(name="By", value=f"{entry.user} | {entry.user.id}", inline=False)
            embed.add_field(name="Reason", value=entry.reason or "*No reason provided*", inline=False)

        await send_log(guild, embed)

    # Member Unbanned
    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        embed = discord.Embed(
            title=":unlock: Member Unbanned",
            color=discord.Color.yellow(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="User", value=f"{user} | {user.id}", inline=False)
        await send_log(guild, embed)

    # Emoji Added / Removed
    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: discord.Guild, before: list[discord.Emoji], after: list[discord.Emoji]):
        added = [e for e in after if e not in before]
        removed = [e for e in before if e not in after]
        
        for emoji in added:
            embed = discord.Embed(
                title=":new: Emoji Added",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Emoji", value=str(emoji), inline=False)
            await send_log(guild, embed)
        
        for emoji in removed:
            embed = discord.Embed(
                title=":regional_indicator_x: Emoji Removed",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Emoji Name", value=emoji.name, inline=False)
            await send_log(guild, embed)

    # --- Commands ---

    @commands.command(name="export_ids")
    async def export_ids(self, ctx: commands.Context):
        """Export all member Discord IDs to a text file (Moderators only)."""

        # Check role
        if not any(role.name == "Moderators" for role in ctx.author.roles):
            await ctx.send("❌ You do not have permission to use this command.", delete_after=5)
            return

        # Defer message
        await ctx.typing()

        # Collect IDs
        ids = [str(member.id) for member in ctx.guild.members if not member.bot]

        # Save file
        filename = f"member_ids_{ctx.guild.id}.txt"
        try:
            with open(filename, "w") as f:
                f.write("\n".join(ids))

            await ctx.send(
                f"✅ Exported {len(ids)} member IDs.",
                file=discord.File(filename)
            )
        except Exception as e:
            await ctx.send(f"❌ An error occurred during export: {e}")
        finally:
            if os.path.exists(filename):
                os.remove(filename)  # Clean up the file from disk

    # --- Error Handlers ---

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """
        Handles errors for app commands *in this cog*.
        Note: The original script had no app commands, so this will only
        fire if you add slash commands to *this specific cog*.
        """
        if isinstance(error, app_commands.CommandNotFound):
            return  # Ignore unknown commands
        
        # Log other errors
        print(f"Error in cog 'Rancour' app command: {error}")
        if interaction.response.is_done():
            await interaction.followup.send("An unknown error occurred.", ephemeral=True)
        else:
            await interaction.response.send_message("An unknown error occurred.", ephemeral=True)
        
        # Re-raise error for potential global handlers
        raise error

# --- Setup Function ---

async def setup(bot: commands.Bot):
    """Adds the cog to the bot."""
    await bot.add_cog(Rancour(bot))
