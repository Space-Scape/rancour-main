import os
import discord
from discord.ext import commands
from discord import app_commands
from oauth2client.service_account import ServiceAccountCredentials
import gspread

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
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

channel_config = {
    "submission": None,
    "review": None,
    "log": None
}

REQUIRED_ROLE_NAME = "Drop Manager"

def user_has_role(user: discord.Member, role_name: str) -> bool:
    return any(role.name == role_name for role in user.roles)

# ---------------------------
# 🔷 Channel Set Logic
# ---------------------------
async def set_channel_logic(interaction_or_ctx, channel_type: str):
    user = getattr(interaction_or_ctx, 'user', interaction_or_ctx.author)
    if not isinstance(user, discord.Member) or not user_has_role(user, REQUIRED_ROLE_NAME):
        await interaction_or_ctx.response.send_message("❌ You do not have permission to use this command.", ephemeral=True) \
            if hasattr(interaction_or_ctx, 'response') else \
            await interaction_or_ctx.send("❌ You do not have permission to use this command.")
        return
    channel_config[channel_type] = interaction_or_ctx.channel.id
    msg = f"✅ This channel set as the **{channel_type}** channel."
    await interaction_or_ctx.response.send_message(msg, ephemeral=True) \
        if hasattr(interaction_or_ctx, 'response') else \
        await interaction_or_ctx.send(msg)

# Slash commands
@tree.command(name="setsubmissionchannel", description="Set the submission channel")
async def slash_set_submission(interaction: discord.Interaction):
    await set_channel_logic(interaction, "submission")

@tree.command(name="setreviewchannel", description="Set the review channel")
async def slash_set_review(interaction: discord.Interaction):
    await set_channel_logic(interaction, "review")

@tree.command(name="setlogchannel", description="Set the log channel")
async def slash_set_log(interaction: discord.Interaction):
    await set_channel_logic(interaction, "log")

# Prefix commands
@bot.command(name="setsubmissionchannel")
async def prefix_set_submission(ctx):
    await set_channel_logic(ctx, "submission")

@bot.command(name="setreviewchannel")
async def prefix_set_review(ctx):
    await set_channel_logic(ctx, "review")

@bot.command(name="setlogchannel")
async def prefix_set_log(ctx):
    await set_channel_logic(ctx, "log")

# ---------------------------
# 🔷 Drop Submission Logic
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

async def bandos_logic(interaction_or_ctx, screenshot):
    if channel_config["submission"] != interaction_or_ctx.channel.id:
        msg = "❌ You can only use this command in the designated drop submission channel."
        await interaction_or_ctx.response.send_message(msg, ephemeral=True) \
            if hasattr(interaction_or_ctx, 'response') else \
            await interaction_or_ctx.send(msg)
        return

    view = DropView(interaction_or_ctx.user if hasattr(interaction_or_ctx, 'user') else interaction_or_ctx.author, screenshot)
    await interaction_or_ctx.response.send_message("📝 Please select the drop received from the dropdown below.", view=view, ephemeral=True) \
        if hasattr(interaction_or_ctx, 'response') else \
        await interaction_or_ctx.send("📝 Please select the drop received from the dropdown below.", view=view)

@tree.command(name="bandos", description="Submit a drop from Bandos")
@app_commands.describe(screenshot="Attach a screenshot of the drop")
async def slash_bandos(interaction: discord.Interaction, screenshot: discord.Attachment):
    await bandos_logic(interaction, screenshot)

@bot.command(name="bandos")
async def prefix_bandos(ctx):
    if not ctx.message.attachments:
        await ctx.send("❌ Please attach a screenshot with your command.")
        return
    await bandos_logic(ctx, ctx.message.attachments[0])

# ---------------------------
# 🔷 Review Buttons
# ---------------------------
class DropReviewButtons(discord.ui.View):
    def __init__(self, user: discord.User, drop: str, image_url: str):
        super().__init__(timeout=None)
        self.user = user
        self.drop = drop
        self.image_url = image_url

    @discord.ui.button(label="Approve ✅", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_channel = bot.get_channel(channel_config["log"])
        if log_channel:
            await log_channel.send(f"✅ **Approved**: {self.drop} for {self.user.mention}")

        sheet.append_row([str(self.user.id), self.drop, self.image_url])
        await interaction.response.send_message("Approved and logged.", ephemeral=True)

    @discord.ui.button(label="Reject ❌", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_channel = bot.get_channel(channel_config["log"])
        if log_channel:
            await log_channel.send(f"❌ **Rejected**: {self.drop} for {self.user.mention}")
        await interaction.response.send_message("Submission rejected.", ephemeral=True)

# ---------------------------
# 🔷 On Ready
# ---------------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    await tree.sync()
    print(f"✅ Slash commands synced.")

bot.run(os.getenv('DISCORD_BOT_TOKEN'))

