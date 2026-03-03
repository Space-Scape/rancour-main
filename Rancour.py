import os
import discord
from discord.ext import commands
from datetime import datetime
from discord import app_commands

# --- Constants ---
LOG_CHANNEL_ID = 1275464228421107713
MESSAGE_LOG_CHANNEL_ID = 1272629843552501805 

# --- Helper Functions ---

def format_dt(dt):
    """Formats a datetime object into a standard string."""
    return dt.strftime("%m/%d/%Y %I:%M %p")

async def send_log(guild: discord.Guild, embed: discord.Embed, channel_id: int = LOG_CHANNEL_ID):
    """Sends an embed to the designated log channel."""
    log_channel = guild.get_channel(channel_id)
    if log_channel:
        try:
            await log_channel.send(embed=embed)
        except discord.Forbidden:
            print(f"Missing permissions to send log in guild: {guild.id} to channel {channel_id}")
        except discord.HTTPException as e:
            print(f"Failed to send log: {e}")

# --- Cog Class ---

class Rancour(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Rancour has been loaded and is ready.")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Role Added
        added_roles = [r for r in after.roles if r not in before.roles]
        for role in added_roles:
            embed = discord.Embed(title=":white_check_mark: Role Added to User", color=discord.Color.green(), timestamp=datetime.utcnow())
            # FIXED: Added display_name
            embed.add_field(name="User", value=f"{after.display_name} ({after}) | {after.id}", inline=False)
            embed.add_field(name="Role", value=role.mention, inline=False)
            await send_log(after.guild, embed)

        # Role Removed
        removed_roles = [r for r in before.roles if r not in after.roles]
        for role in removed_roles:
            embed = discord.Embed(title=":x: Role Removed from User", color=discord.Color.red(), timestamp=datetime.utcnow())
            # FIXED: Added display_name
            embed.add_field(name="User", value=f"{after.display_name} ({after}) | {after.id}", inline=False)
            embed.add_field(name="Role", value=role.mention, inline=False)
            await send_log(after.guild, embed)

        # Nickname Changed
        if before.nick != after.nick:
            embed = discord.Embed(title=":pencil: Nickname Changed", color=discord.Color.orange(), timestamp=datetime.utcnow())
            # FIXED: Shows the current display_name
            embed.add_field(name="User", value=f"{after.display_name} ({after}) | {after.id}", inline=False)
            embed.add_field(name="Old Nickname", value=before.nick or "*None*", inline=True)
            embed.add_field(name="New Nickname", value=after.nick or "*None*", inline=True)
            await send_log(after.guild, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or before.content == after.content or not before.guild:
            return

        embed = discord.Embed(title=":pencil: Message Updated", color=discord.Color.gold(), timestamp=datetime.utcnow())
        embed.add_field(name="Old Message", value=before.content or "*no content*", inline=False)
        embed.add_field(name="New Message", value=after.content or "*no content*", inline=False)
        embed.add_field(name="Channel", value=before.channel.mention, inline=True)
        # FIXED: Shows nickname in message logs
        embed.add_field(name="Author", value=f"{before.author.display_name} ({before.author}) | {before.author.id}", inline=True)
        await send_log(before.guild, embed, MESSAGE_LOG_CHANNEL_ID)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        embed = discord.Embed(title=":wastebasket: Message Deleted", color=discord.Color.dark_red(), timestamp=datetime.utcnow())
        embed.add_field(name="Deleted Message", value=message.content or "*no content*", inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        # FIXED: Shows nickname in delete logs
        embed.add_field(name="Author", value=f"{message.author.display_name} ({message.author}) | {message.author.id}", inline=True)
        await send_log(message.guild, embed, MESSAGE_LOG_CHANNEL_ID)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        embed = discord.Embed(title=":wave: Member Joined", color=discord.Color.green(), timestamp=datetime.utcnow())
        # FIXED: Added display_name
        embed.add_field(name="User", value=f"{member.display_name} ({member}) | {member.id}", inline=False)
        embed.add_field(name="Account Created", value=format_dt(member.created_at), inline=False)
        await send_log(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        entry = None
        try:
            async for log in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
                if log.target.id == member.id and (datetime.utcnow() - log.created_at).total_seconds() < 5:
                    entry = log
                    break
        except discord.Forbidden: pass

        embed = discord.Embed(timestamp=datetime.utcnow())
        # FIXED: Added display_name
        embed.add_field(name="User", value=f"{member.display_name} ({member}) | {member.id}", inline=False)

        if entry:
            embed.title = ":anger: Member Kicked"
            embed.color = discord.Color.dark_red()
            embed.add_field(name="By", value=f"{entry.user.display_name} ({entry.user})", inline=False)
            embed.add_field(name="Reason", value=entry.reason or "*No reason provided*", inline=False)
        else:
            embed.title = ":saluting_face: Member Left"
            embed.color = discord.Color.red()
        await send_log(guild, embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot: return

        embed = discord.Embed(timestamp=datetime.utcnow())
        # FIXED: Added display_name to voice logs
        user_val = f"{member.display_name} ({member}) | {member.id}"

        if before.channel is None and after.channel is not None:
            embed.title, embed.color = ":microphone2: Voice Channel Joined", discord.Color.green()
            embed.add_field(name="User", value=user_val, inline=False)
            embed.add_field(name="Channel", value=after.channel.mention, inline=False)
            await send_log(member.guild, embed)
        elif before.channel is not None and after.channel is None:
            embed.title, embed.color = ":mute: Voice Channel Left", discord.Color.red()
            embed.add_field(name="User", value=user_val, inline=False)
            embed.add_field(name="Channel", value=before.channel.mention, inline=False)
            await send_log(member.guild, embed)
        elif before.channel and after.channel and before.channel != after.channel:
            embed.title, embed.color = ":arrow_right_hook: Voice Channel Switched", discord.Color.blue()
            embed.add_field(name="User", value=user_val, inline=False)
            embed.add_field(name="Old Channel", value=before.channel.mention, inline=True)
            embed.add_field(name="New Channel", value=after.channel.mention, inline=True)
            await send_log(member.guild, embed)

    @commands.command(name="export_ids")
    async def export_ids(self, ctx: commands.Context):
        if not any(role.name == "Moderators" for role in ctx.author.roles):
            await ctx.send("❌ You do not have permission.", delete_after=5)
            return
        await ctx.typing()
        ids = [str(m.id) for m in ctx.guild.members if not m.bot]
        filename = f"member_ids_{ctx.guild.id}.txt"
        with open(filename, "w") as f: f.write("\n".join(ids))
        await ctx.send(f"✅ Exported {len(ids)} member IDs.", file=discord.File(filename))
        os.remove(filename)

async def setup(bot: commands.Bot):
    await bot.add_cog(Rancour(bot))
