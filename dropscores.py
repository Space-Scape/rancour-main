import os
import discord
from discord.ext import commands
from discord import app_commands
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from datetime import datetime, timezone

# ---------------------------
# 🔹 Google Sheets Setup
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
# 🔹 Discord Bot Setup
# ---------------------------
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ---------------------------
# 🔹 Channel IDs + Role
# ---------------------------
SUBMISSION_CHANNEL_ID = 1391921214909579336
REVIEW_CHANNEL_ID = 1391921254034047066
LOG_CHANNEL_ID = 1391921275332722749
REQUIRED_ROLE_NAME = "Drop Manager"

# ---------------------------
# 🔹 Boss-Drop Mapping
# ---------------------------
boss_drops = {
    "Bandos": ["Bandos Chestplate", "Bandos Tassets", "Bandos Boots", "Godsword Shard 1", "Godsword Shard 2", "Godsword Shard 3", "Bandos Hilt"],
    "Zulrah": ["Tanzanite Fang", "Magic Fang", "Serpentine Visage", "Uncut Onyx"],
    "Corporeal Beast": ["Elysian Sigil", "Spectral Sigil", "Arcane Sigil", "Spirit Shield"]
    "Barrows": ["Ahrim’s hood", "Ahrim’s robetop", "Ahrim’s robeskirt", "Ahrim’s staff",”Karil’s coif”, “Karil’s leathertop”, “Karil’s leatherskirt”, “Karil’s crossbow”, “Dharok’s helm”, “Dharok’s platebody”, Dharok’s platelegs”, Dharok’s greataxe”, “Guthan’s helm”, “guthan’s platebody”, “Guthan’s chainskirt”, “Guthan’s warspear”, “torag’s helm”, “Torag’s platebody”, “Torag’s platelegs”, “Torag’s hammer”, “Verac’s helm”, “Verac’s brassard”, “Verac’s plateskirt”, “Verac’s flail”],
    "Scurrius": ["Scurrius’ spine", "Scurry"],
    "Giant mole": ["Baby mole", "Mole skin", "Mole claw"],
    "Deranged Archaeologist": ["Steel ring"],
    "Dagannoth kings": ["Pet dagannoth supreme", "Archers ring", "Dragon axe", "Seercull", “Pet dagannoth rex”, “Berserker ring”, “Warrior ring”, “Pet dagannoth prime”, “Seers ring”, “Mud battlestaff”],

    # Add more bosses as needed
}

# ---------------------------
# 🔹 Dynamic Drop Submission
# ---------------------------
class BossSelect(discord.ui.Select):
    def __init__(self, user, screenshot, page, max_pages):
        self.user = user
        self.screenshot = screenshot
        self.page = page
        self.max_pages = max_pages
        bosses = list(boss_drops.keys())
        start = page * 25
        end = start + 25
        options = [discord.SelectOption(label=boss) for boss in bosses[start:end]]
        super().__init__(placeholder="Select a boss", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=DropView(self.user, self.screenshot, self.values[0]))


class BossView(discord.ui.View):
    def __init__(self, user, screenshot, page=0):
        super().__init__()
        self.user = user
        self.screenshot = screenshot
        self.page = page
        max_pages = (len(boss_drops) - 1) // 25
        self.add_item(BossSelect(user, screenshot, page, max_pages))
        if page > 0:
            self.add_item(PreviousPageButton(user, screenshot, page))
        if page < max_pages:
            self.add_item(NextPageButton(user, screenshot, page))


class PreviousPageButton(discord.ui.Button):
    def __init__(self, user, screenshot, page):
        super().__init__(label="◀️ Previous", style=discord.ButtonStyle.secondary)
        self.user = user
        self.screenshot = screenshot
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=BossView(self.user, self.screenshot, self.page - 1))


class NextPageButton(discord.ui.Button):
    def __init__(self, user, screenshot, page):
        super().__init__(label="Next ▶️", style=discord.ButtonStyle.secondary)
        self.user = user
        self.screenshot = screenshot
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=BossView(self.user, self.screenshot, self.page + 1))


class DropSelect(discord.ui.Select):
    def __init__(self, user, screenshot, boss):
        self.user = user
        self.screenshot = screenshot
        self.boss = boss
        options = [discord.SelectOption(label=drop) for drop in boss_drops[boss]]
        super().__init__(placeholder=f"Select a drop from {boss}", options=options)

    async def callback(self, interaction: discord.Interaction):
        review_channel = bot.get_channel(REVIEW_CHANNEL_ID)
        embed = discord.Embed(title=f"{self.boss} Drop Submission", colour=discord.Colour.blurple())
        embed.add_field(name="Submitted For", value=f"{self.user.display_name} ({self.user.id})", inline=False)
        embed.add_field(name="Drop Received", value=self.values[0], inline=False)
        embed.set_image(url=self.screenshot.url)

        view = DropReviewButtons(self.user, self.values[0], self.screenshot.url)
        await review_channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Submitted for review.", ephemeral=True)


class DropView(discord.ui.View):
    def __init__(self, user, screenshot, boss):
        super().__init__()
        self.add_item(DropSelect(user, screenshot, boss))


@tree.command(name="submitdrop", description="Submit a boss drop for review")
@app_commands.describe(screenshot="Attach a screenshot of your drop")
async def submit_drop(interaction: discord.Interaction, screenshot: discord.Attachment):
    if interaction.channel.id != SUBMISSION_CHANNEL_ID:
        await interaction.response.send_message("❌ This command can only be used in the drop submission channel.", ephemeral=True)
        return

    await interaction.response.send_message("Select the boss you received the drop from:", view=BossView(interaction.user, screenshot), ephemeral=True)

# ---------------------------
# 🔹 Review Buttons
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
            embed = discord.Embed(title="Drop Approved", colour=discord.Colour.green())
            embed.add_field(name="Approved By", value=interaction.user.display_name, inline=False)
            embed.add_field(name="Drop For", value=self.submitted_user.mention, inline=False)
            embed.add_field(name="Drop", value=self.drop, inline=False)
            embed.set_image(url=self.image_url)
            await log_channel.send(embed=embed)

        sheet.append_row([
            interaction.user.display_name,
            self.submitted_user.display_name,
            str(self.submitted_user.id),
            self.drop,
            self.image_url,
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        ])

        for child in self.children:
            child.disabled = True

        await interaction.message.edit(view=self)
        await interaction.response.send_message("✅ Approved and logged.", ephemeral=True)

    @discord.ui.button(label="Reject ❌", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.has_drop_manager_role(interaction.user):
            await interaction.response.send_message("❌ You do not have permission to reject.", ephemeral=True)
            return

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(title="Drop Rejected", colour=discord.Colour.red())
            embed.add_field(name="Rejected By", value=interaction.user.display_name, inline=False)
            embed.add_field(name="Drop For", value=self.submitted_user.mention, inline=False)
            embed.add_field(name="Drop", value=self.drop, inline=False)
            embed.set_image(url=self.image_url)
            await log_channel.send(embed=embed)

        for child in self.children:
            child.disabled = True

        await interaction.message.edit(view=self)
        await interaction.response.send_message("❌ Submission rejected.", ephemeral=True)

# ---------------------------
# 🔹 On Ready
# ---------------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    synced = await tree.sync()
    print(f"✅ Synced {len(synced)} slash commands.")

bot.run(os.getenv('DISCORD_BOT_TOKEN'))
