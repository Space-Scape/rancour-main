import os
import discord
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Button
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Google Sheets Setup
SCOPE = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']

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
    "client_x509_cert_url": os.getenv('GOOGLE_CLIENT_X509_CERT_URL')
}

CREDS = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, SCOPE)
CLIENT = gspread.authorize(CREDS)
DROP_SHEET = CLIENT.open("Image Upload Test").worksheet("Drop Submissions")

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Store user image uploads
user_submissions = {}

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
            embed = discord.Embed(title=f"Drop Submission for {self.boss_name}")
            embed.add_field(name="Account Name", value=self.user_nickname)
            embed.add_field(name="Drop", value=self.drop_name.value)
            embed.set_image(url=self.image_url)
            embed.set_footer(text="Click the appropriate button below to verify this submission.")

            drop_channel = discord.utils.get(interaction.guild.text_channels, name="drop-submissions")
            if drop_channel:
                await drop_channel.send(embed=embed, view=VerificationView(self.user_nickname, self.drop_name.value, self.image_url))
                await interaction.response.send_message("Drop submission successful!", ephemeral=True)
            else:
                await interaction.response.send_message("Error: drop-submissions channel not found.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred during submission: {e}", ephemeral=True)
            print(f"Error during drop submission: {e}")

class VerificationView(View):
    def __init__(self, account_name, drop_name, image_url):
        super().__init__(timeout=None)
        self.account_name = account_name
        self.drop_name = drop_name
        self.image_url = image_url

    async def verify_or_reject(self, interaction: discord.Interaction, verified_status: str):
        required_roles = {"Clan Staff", "Server Admin", "Moderator", "Event Planner"}
        user_roles = {role.name for role in interaction.user.roles}

        if required_roles.intersection(user_roles):
            if verified_status == "Y":
                await interaction.response.send_message(f"Submission verified by {interaction.user.mention}", ephemeral=False)
            else:
                await interaction.response.send_message(f"Submission rejected by {interaction.user.mention}", ephemeral=False)
            self.log_to_sheet(verified_status)
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
            DROP_SHEET.append_row([
                self.account_name,
                self.drop_name,
                verified_status,
                str(datetime.now()),
                self.image_url
            ])
            print(f"Logged to Drop Submissions: {self.account_name}, {self.drop_name}, {verified_status}")
        except Exception as e:
            print(f"Error logging to sheet: {e}")

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
    if isinstance(message.channel, discord.DMChannel):
        return

    if message.channel.name == "drop-submissions" and message.attachments:
        user_submissions[message.author.id] = (message.author.display_name, message.attachments[0].url)
        print(f"Stored image URL: {message.attachments[0].url}")
        await message.channel.send(f"{message.author.mention}, your image has been recorded.", delete_after=10)

        view = View()
        bosses = [
            {"name": "Bandos", "emoji_name": "graardor"},
            {"name": "Zammy", "emoji_name": "zammy"},
            {"name": "Sara", "emoji_name": "sara"},
            {"name": "Arma", "emoji_name": "arma"},
            {"name": "Nex", "emoji_name": "nex"}
        ]

        for boss in bosses:
            emoji = discord.utils.get(message.guild.emojis, name=boss["emoji_name"]) or "🎯"
            button = DropSubmissionButton(label=boss["name"], emoji=emoji, boss_name=boss["name"])
            view.add_item(button)

        await message.channel.send("Choose a boss to submit a drop for:", view=view)

    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")

bot.run(os.getenv('DISCORD_BOT_TOKEN'))
