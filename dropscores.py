import os
import discord
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Button
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets Setup



import discord
from discord.ext import commands
from discord import app_commands
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os

# -------- Load Google Sheet Credentials --------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("google_creds.json", scope)
sheet_client = gspread.authorize(creds)
sheet = sheet_client.open("Bandos Drops").sheet1

credentials_dict = {
    "type": os.getenv('GOOGLE_TYPE'),
    "project_id": os.getenv('GOOGLE_PROJECT_ID'),
    "private_key_id": os.getenv('GOOGLE_PRIVATE_KEY_ID'),
    "private_key": os.getenv('GOOGLE_PRIVATE_KEY').replace("\\n", "\n"),
    "client_email": os.getenv('GOOGLE_CLIENT_EMAIL'),
    "client_id": os.getenv('GOOGLE_CLIENT_ID'),
    "auth_uri": os.getenv('GOOGLE_AUTH_URI'),
    "token_uri": os.getenv('GOOGLE_TOKEN_URI'),
    "auth_provider_x509_cert_url": os.getenv('GOOGLE_AUTH_PROVIDER_X509_CERT_URL'),
    "client_x509_cert_url": os.getenv('GOOGLE_CLIENT_X509_CERT_URL'),
    "universe_domain": os.getenv('GOOGLE_UNIVERSE_DOMAIN'),
    "sheet_id": os.getenv('GOOGLE_SHEET_ID')
}

# -------- Bot Setup --------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# In-memory channel tracking (persist as needed)
channel_config = {
    "submission": None,
    "review": None,
    "log": None
}

# -------- Channel Set Commands --------
@tree.command(name="setsubmissionchannel", description="Set the submission channel")
@app_commands.checks.has_permissions(administrator=True)
async def set_submission(interaction: discord.Interaction):
    channel_config["submission"] = interaction.channel.id
    await interaction.response.send_message("✅ This channel set as the submission channel.", ephemeral=True)

@tree.command(name="setreviewchannel", description="Set the review channel")
@app_commands.checks.has_permissions(administrator=True)
async def set_review(interaction: discord.Interaction):
    channel_config["review"] = interaction.channel.id
    await interaction.response.send_message("✅ This channel set as the review channel.", ephemeral=True)

@tree.command(name="setlogchannel", description="Set the log channel")
@app_commands.checks.has_permissions(administrator=True)
async def set_log(interaction: discord.Interaction):
    channel_config["log"] = interaction.channel.id
    await interaction.response.send_message("✅ This channel set as the log channel.", ephemeral=True)

# -------- Drop Submission Command --------
class DropSelection(discord.ui.Select):
    def __init__(self, user: discord.User, attachment: discord.Attachment):
        self.user = user
        self.attachment = attachment

        options = [
            discord.SelectOption(label="Bandos Chestplate"),
            discord.SelectOption(label="Bandos Tassets"),
            discord.SelectOption(label="Bandos Boots"),
            discord.SelectOption(label="Godsword Shard 1"),
            discord.SelectOption(label="Godsword Shard 2"),
            discord.SelectOption(label="Godsword Shard 3"),
            discord.SelectOption(label="Bandos Hilt")
        ]

        super().__init__(placeholder="Select your Bandos drop", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        review_channel = bot.get_channel(channel_config["review"])
        if not review_channel:
            await interaction.response.send_message("❌ Review channel not set.", ephemeral=True)
            return

        embed = discord.Embed(title="Bandos Drop Submission", colour=discord.Colour.blue())
        embed.add_field(name="User", value=f"{self.user.name} ({self.user.id})", inline=False)
        embed.add_field(name="Drop", value=self.values[0], inline=False)
        embed.set_image(url=self.attachment.url)

        view = DropReviewButtons(self.user, self.values[0], self.attachment.url)
        await review_channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Submission sent for review.", ephemeral=True)

class DropView(discord.ui.View):
    def __init__(self, user, attachment):
        super().__init__()
        self.add_item(DropSelection(user, attachment))

@tree.command(name="bandos", description="Submit a drop from Bandos")
@app_commands.describe(screenshot="Attach a screenshot of the drop")
async def bandos(interaction: discord.Interaction, screenshot: discord.Attachment):
    if channel_config["submission"] != interaction.channel.id:
        await interaction.response.send_message("❌ You can only use this command in the designated drop submission channel.", ephemeral=True)
        return

    view = DropView(interaction.user, screenshot)
    await interaction.response.send_message("📝 Please select the drop received from the dropdown below.", view=view, ephemeral=True)

# -------- Buttons for Approve / Reject --------
class DropReviewButtons(discord.ui.View):
    def __init__(self, user: discord.User, drop: str, image_url: str):
        super().__init__(timeout=None)
        self.user = user
        self.drop = drop
        self.image_url = image_url

    @discord.ui.button(label="Approve ✅", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_channel = bot.get_channel(channel_config["log"])
        await log_channel.send(f"✅ **Approved**: {self.drop} for {self.user.mention}")

        # Append to Google Sheet
        sheet.append_row([str(self.user.id), self.drop, self.image_url])
        await interaction.response.send_message("Approved and logged.", ephemeral=True)

    @discord.ui.button(label="Reject ❌", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_channel = bot.get_channel(channel_config["log"])
        await log_channel.send(f"❌ **Rejected**: {self.drop} for {self.user.mention}")
        await interaction.response.send_message("Submission rejected.", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

bot.run(os.getenv('DISCORD_BOT_TOKEN'))
