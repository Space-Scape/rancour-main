import os
import json
import base64
import discord
from discord.ext import commands, tasks
from discord.ui import Modal, TextInput, View, Button
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import asyncio

# Google Sheets Setup
SCOPE = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']

# Decode the environment variable
credentials_json = base64.b64decode(os.getenv('GOOGLE_CREDENTIALS_JSON')).decode('utf-8')

# Load the credentials from the decoded JSON
CREDS = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(credentials_json), SCOPE)

CLIENT = gspread.authorize(CREDS)
DROP_SHEET = CLIENT.open("Image Upload Test").worksheet("Drop Submissions")
HIGHSCORE_SHEET = CLIENT.open("Image Upload Test").worksheet("Hiscores")

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Global dictionary to store user image URLs and nicknames
user_submissions = {}

# Mapping abbreviations to full boss names
BOSS_NAME_MAP = {
    "cox": "chambers of xeric",
    "cm": "chambers of xeric challenge mode",
    "tob": "theatre of blood",
    "hmt": "theatre of blood hard mode",
    "toa": "tombs of amascut",
    "extoa": "tombs of amascut expert mode",
    "zulrah": "zulrah",
    "vorkath": "vorkath",
    "muspah": "phantom muspah",
    "nm": "the nightmare",
    "pnm": "phosani's nightmare",
    "duke": "duke sucellus",
    "leviathan": "leviathan",
    "whisperer": "whisperer",
    "vardorvis": "vardorvis",
    "awakened duke": "awakened duke sucellus",
    "awakened levi": "awakened leviathan",
    "awakened whisp": "awakened whisperer",
    "awakened vard": "awakened vardorvis",
    "jad": "tztok-jad",
    "zuk": "tzkal-zuk",
    "inferno": "tzkal-zuk",
    "sol": "colosseum",
    "sol heredit": "colosseum",
    "colo": "colosseum",
    "col": "colosseum",
}

def get_full_boss_name(abbreviation):
    return BOSS_NAME_MAP.get(abbreviation.lower(), abbreviation)

def parse_time(time_str):
    # Handle times in "HH:MM:SS", "MM:SS", or "SS.xx" format
    parts = time_str.split(':')
    
    try:
        if len(parts) == 3:  # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:  # MM:SS or MM:SS.xx
            return int(parts[0]) * 60 + float(parts[1])
        else:  # SS.xx format or just seconds
            return float(time_str)
    except ValueError:
        return float('inf')  # Return a high value if parsing fails

class HighscoreSubmissionModal(Modal):
    def __init__(self, user_nickname, image_url):
        super().__init__(title=f"Submit Hiscore")
        self.user_nickname = user_nickname
        self.image_url = image_url

        self.player_name = TextInput(label="Player Name", placeholder="Enter full Player RSN's", required=True)
        self.add_item(self.player_name)

        self.boss_name = TextInput(label="Boss Name", placeholder="Enter the boss name", required=True)
        self.add_item(self.boss_name)

        self.team_size = TextInput(label="Team Size (Leave blank if solo)", placeholder="Enter the team size", required=False)
        self.add_item(self.team_size)

        self.time = TextInput(label="Time", placeholder="Enter the time (e.g., 17:00)", required=True)
        self.add_item(self.time)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Convert abbreviation to full boss name
            full_boss_name = get_full_boss_name(self.boss_name.value)

            # List players without mentions
            players = [player.strip() for player in self.player_name.value.split(",")]
            player_list = ", ".join(players)

            # Create an embed with the submission details for staff verification
            embed = discord.Embed(title=f"Hiscore Submission for {full_boss_name}")
            embed.add_field(name="Player Name", value=player_list)
            embed.add_field(name="Boss Name", value=full_boss_name)
            embed.add_field(name="Team Size", value=self.team_size.value if self.team_size.value else "N/A")
            embed.add_field(name="Time", value=self.time.value)
            embed.set_image(url=self.image_url)
            embed.set_footer(text="Click the appropriate button below to verify this submission.")

            # Send the embed to the speed-times channel
            drop_channel = discord.utils.get(interaction.guild.text_channels, name="speed-times")
            if drop_channel:
                await drop_channel.send(embed=embed, view=VerificationView(self.player_name.value, full_boss_name, self.team_size.value if self.team_size.value else "N/A", self.time.value, self.image_url, is_highscore=True))
                await interaction.response.send_message(f"Hiscore submission successful! Players listed: {player_list}", ephemeral=False)
            else:
                await interaction.response.send_message(f"Error: speed-times channel not found.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred during submission: {e}", ephemeral=True)
            print(f"Error during hiscore submission: {e}")

class DropSubmissionModal(Modal):
    def __init__(self, boss_name, user_nickname, image_url):
        super().__init__(title=f"Submit Drop for {boss_name}")
        self.boss_name = boss_name
        self.user_nickname = user_nickname
        self.image_url = image_url

        self.drop_name = TextInput(label="Drop Name", placeholder="Enter the name of the drop", required=True)
        self.add_item(self.drop_name)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Create an embed with the submission details for staff verification
            embed = discord.Embed(title=f"Drop Submission for {self.boss_name}")
            embed.add_field(name="Account Name", value=self.user_nickname)
            embed.add_field(name="Drop", value=self.drop_name.value)
            embed.set_image(url=self.image_url)
            embed.set_footer(text="Click the appropriate button below to verify this submission.")

            # Send the embed to the drop-submissions channel
            drop_channel = discord.utils.get(interaction.guild.text_channels, name="drop-submissions")
            if drop_channel:
                await drop_channel.send(embed=embed, view=VerificationView(self.user_nickname, self.drop_name.value, self.image_url))
                await interaction.response.send_message("Drop submission successful!", ephemeral=True)
            else:
                await interaction.response.send_message(f"Error: Drop-submissions channel not found.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred during submission: {e}", ephemeral=True)
            print(f"Error during drop submission: {e}")

class VerificationView(View):
    def __init__(self, account_name, boss_name, team_size=None, time=None, image_url=None, is_highscore=False):
        super().__init__(timeout=None)
        self.account_name = account_name
        self.boss_name = boss_name
        self.team_size = team_size
        self.time = time
        self.image_url = image_url
        self.is_highscore = is_highscore

    async def verify_or_reject(self, interaction: discord.Interaction, verified_status: str):
        # Check if the user has one of the required roles
        required_roles = {"Clan Staff", "Server Admin", "Moderator", "Event Planner"}
        user_roles = {role.name for role in interaction.user.roles}

        if required_roles.intersection(user_roles):
            if verified_status == "Y":
                await interaction.response.send_message(f"Submission verified by {interaction.user.mention}", ephemeral=False)
            else:
                await interaction.response.send_message(f"Submission rejected by {interaction.user.mention}", ephemeral=False)
            await self.log_to_sheet(verified_status)

            # Trigger the update of hiscores in the hiscores channel after verification
            if self.is_highscore and verified_status == "Y":
                await self.update_hiscores(interaction.guild, self.boss_name, self.team_size)
        else:
            await interaction.response.send_message("You don't have permission to verify or reject submissions.", ephemeral=True)

    @discord.ui.button(label="Verify", style=discord.ButtonStyle.success, emoji="✅")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.verify_or_reject(interaction, "Y")

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger, emoji="❌")
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.verify_or_reject(interaction, "N")

    def log_to_sheet(self, verified_status):
        try:
            if self.is_highscore:
                # Log to Hiscores sheet
                HIGHSCORE_SHEET.append_row([
                    self.account_name, self.boss_name, self.team_size,
                    self.time, verified_status, str(datetime.now()), self.image_url
                ])
                print(f"Logged to Hiscores sheet: {self.account_name, self.boss_name, self.team_size, self.time, verified_status, self.image_url}")
            else:
                # Log to Drop Submissions sheet
                DROP_SHEET.append_row([
                    self.account_name,  # Assuming user_nickname is the account name
                    self.boss_name,     # The name of the drop
                    verified_status,
                    str(datetime.now()), 
                    self.image_url  # This is where the image URL should be logged
                ])
                print(f"Logged to Drop Submissions sheet: {self.account_name, self.boss_name, verified_status, self.image_url}")
        except Exception as e:
            print(f"Error logging to sheet: {e}")

    # Function to update hiscores
    async def update_hiscores(self, guild, boss_name, team_size):
        channel = discord.utils.get(guild.text_channels, name="hiscores")
        if not channel:
            print("Channel not found: hiscores")
            return

        # Delete previous messages containing the boss name
        async for message in channel.history(limit=100):
            if boss_name.lower() in message.content.lower():
                await message.delete()

        # Post the updated hiscores
        ctx = await bot.get_context(channel.last_message)
        await ctx.invoke(bot.get_command("hiscores"), boss_mode=boss_name.lower(), team_size=team_size)

class SubmitHighscoreButton(Button):
    def __init__(self, label, emoji):
        super().__init__(label=label, style=discord.ButtonStyle.primary, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id in user_submissions:
            user_nickname, image_url = user_submissions[user_id]
            modal = HighscoreSubmissionModal(user_nickname, image_url)
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("You haven't uploaded an image yet. Please upload one before submitting.", ephemeral=True)

class DropSubmissionButton(Button):
    def __init__(self, label, emoji, boss_name):
        super().__init__(label=label, style=discord.ButtonStyle.primary, emoji=emoji)
        self.boss_name = boss_name

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        if user_id in user_submissions:
            user_nickname, image_url = user_submissions[user_id]
            modal = DropSubmissionModal(self.boss_name, user_nickname, image_url)
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("You haven't uploaded an image yet. Please upload one before submitting.", ephemeral=True)

@bot.event
async def on_message(message):
    # Check if the message is in a guild (server) channel
    if isinstance(message.channel, discord.DMChannel):
        return  # Ignore DMs

    # Check if the message contains an image and is in the correct channel for drops
    if message.channel.name == "drop-submissions" and message.attachments:
        user_submissions[message.author.id] = (message.author.display_name, message.attachments[0].url)
        print(f"Stored image URL: {message.attachments[0].url}")
        await message.channel.send(f"{message.author.mention}, your image has been recorded.", delete_after=10)

        # Trigger the drop submission buttons
        view = View()
        bosses = [
            {"name": "Bandos", "emoji_name": "graardor"},
            {"name": "Zammy", "emoji_name": "zammy"},
            {"name": "Sara", "emoji_name": "sara"},
            {"name": "Arma", "emoji_name": "arma"},
            {"name": "Nex", "emoji_name": "nex"}
        ]

        for boss in bosses:
            emoji = discord.utils.get(message.guild.emojis, name=boss["emoji_name"]) or "<:graardor:123456789012345678>"
            button = DropSubmissionButton(label=boss["name"], emoji=emoji, boss_name=boss["name"])
            view.add_item(button)

        await message.channel.send("Choose a boss to submit a drop for:", view=view)

    # Check if the message contains an image and is in the correct channel for highscores
    elif message.channel.name == "speed-times" and message.attachments:
        user_submissions[message.author.id] = (message.author.display_name, message.attachments[0].url)
        print(f"Stored image URL: {message.attachments[0].url}")
        await message.channel.send(f"{message.author.mention}, your image has been recorded.", delete_after=10)

        # Trigger the hiscore submission button
        view = View()
        submit_button = SubmitHighscoreButton(label="Submit Hiscore", emoji="⏱️")
        view.add_item(submit_button)
        await message.channel.send("Click the button below to provide details for the hiscore submission. Please note that these are for times gained within the clan and are meant to track clan bests, not personal bests:", view=view)

    await bot.process_commands(message)

# Purge speed-times channel every hour
@tasks.loop(hours=1)
async def purge_speed_times():
    channel = discord.utils.get(bot.get_all_channels(), name="speed-times")
    if channel:
        await channel.purge(limit=None)
        print(f"Purged all messages in {channel.name}")
    else:
        print("Channel not found: speed-times")

@purge_speed_times.before_loop
async def before_purge():
    await bot.wait_until_ready()
    print("Waiting for bot to be ready before starting the purge task...")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")
    purge_speed_times.start()

# Command to show the top hiscores
@bot.command()
async def hiscores(ctx, boss_mode: str, team_size: int = None):
    # Normalize boss mode for easier matching
    boss_mode = boss_mode.lower()

    # Identify specific bosses and modes
    boss_name = get_full_boss_name(boss_mode)

    # Fetch records from Google Sheets
    try:
        records = HIGHSCORE_SHEET.get_all_records()
        boss_times = [(record.get('Player Name'), record.get('Time')) for record in records if record.get('Boss Name', '').lower() == boss_name and (record.get('Team Size', '') == "N/A" or int(record.get('Team Size', 0)) == team_size)]
    except Exception as e:
        await ctx.send(f"An error occurred while fetching hiscores: {e}")
        return

    # Sort by best times (lower is better)
    boss_times.sort(key=lambda x: parse_time(x[1]))

    # If no PBs found
    if not boss_times:
        await ctx.send(f"No hiscores found for {boss_name} with {team_size} players.")
        return

    # Create an embed message with the top 10 PBs
    custom_stopwatch_emoji = discord.utils.get(ctx.guild.emojis, name="stopwatch")
    embed = discord.Embed(
        title=f"{custom_stopwatch_emoji} {boss_name.capitalize()} {f'Team Size: {team_size} |' if team_size else '|'} Top Times {custom_stopwatch_emoji}",
        description="\n".join([f"**{i+1}:** {pb[0]} - {pb[1]}" for i, pb in enumerate(boss_times[:10])]),
        color=discord.Color.gold()
    )

    await ctx.send(embed=embed)

# Command to show a list of all boss abbreviations
@bot.command()
async def hiscores_list(ctx):
    abbreviations = "\n".join([f"{key.upper()}: {value.title()}" for key, value in BOSS_NAME_MAP.items()])
    embed = discord.Embed(
        title="Boss Abbreviations",
        description=abbreviations,
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

bot.run(os.getenv('DISCORD_BOT_TOKEN'))
