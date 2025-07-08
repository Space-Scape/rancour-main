import os
import discord
from discord.ext import commands
from discord import app_commands
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from datetime import datetime

# ---------------------------
# 🔷 Google Sheets Setup
# ---------------------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

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
}

creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
sheet_client = gspread.authorize(creds)

sheet_id = os.getenv("GOOGLE_SHEET_ID")
sheet = sheet_client.open_by_key(sheet_id).sheet1

# ---------------------------
# 🔷 Discord Bot Setup
# ---------------------------
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ---------------------------
# 🔷 Channel IDs + Role
# ---------------------------
SUBMISSION_CHANNEL_ID = 1391921214909579336
REVIEW_CHANNEL_ID = 1391921254034047066
LOG_CHANNEL_ID = 1391921275332722749
REQUIRED_ROLE_NAME = "Drop Manager"

# ---------------------------
# 🔷 Drop Submission Command
# ---------------------------
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
        review_channel = bot.get_channel(REVIEW_CHANNEL_ID)
        if not review_channel:
            await interaction.response.send_message("❌ Review channel not found.", ephemeral=True)
            return

        embed = discord.Embed(title="Bandos Drop Submission", colour=discord.Colour.blue())
        embed.add_field(name="Submitted For", value=f"{self.user.display_name} ({self.user.id})", inline=False)
        embed.add_field(name="Drop Received", value=self.values[0], inline=False)
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
async def slash_bandos(interaction: discord.Interaction, screenshot: discord.Attachment):
    if interaction.channel.id != SUBMISSION_CHANNEL_ID:
        await interaction.response.send_message(
            "❌ You can only use this command in the designated drop submission channel.",
            ephemeral=True
        )
        return

    view = DropView(interaction.user, screenshot)
    await interaction.response.send_message(
        "📝 Please select the drop received from the dropdown below.", view=view, ephemeral=True
    )

# ---------------------------
# 🔷 Review Buttons
# ---------------------------
class DropReviewButtons(discord.ui.View):
    def __init__(self, user: discord.User, drop: str, image_url: str):
        super().__init__(timeout=None)
        self.submitted_user = user
        self.drop = drop
        self.image_url = image_url

    def has_drop_manager_role(self, member: discord.Member) -> bool:
        return any(role.name == REQUIRED_ROLE_NAME for role in member.roles)

    @discord.ui.button(label="Approve ✅", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.has_drop_manager_role(interaction.user):
            await interaction.response.send_message("❌ You do not have permission to approve.", ephemeral=True)
            return

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f"✅ **Approved**: {self.drop} for {self.submitted_user.mention} by {interaction.user.mention}")

        # Append to sheet
        sheet.append_row([
            self.submitted_user.display_name,                # Submitted For
            str(self.submitted_user.id),                    # Submitted For Discord ID
            self.drop,                                      # Drop Received
            self.image_url,                                 # Screenshot Link
            interaction.user.display_name,                  # Approved By
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") # Date/Time
        ])
        await interaction.response.send_message("✅ Approved and logged.", ephemeral=True)

    @discord.ui.button(label="Reject ❌", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.has_drop_manager_role(interaction.user):
            await interaction.response.send_message("❌ You do not have permission to reject.", ephemeral=True)
            return

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f"❌ **Rejected**: {self.drop} for {self.submitted_user.mention} by {interaction.user.mention}")

        await interaction.response.send_message("❌ Submission rejected.", ephemeral=True)

# ---------------------------
# 🔷 On Ready
# ---------------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    synced = await tree.sync()
    print(f"✅ Synced {len(synced)} slash commands.")

bot.run(os.getenv('DISCORD_BOT_TOKEN'))



