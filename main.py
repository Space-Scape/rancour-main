import os
import discord
from discord.ext import commands
from discord import app_commands
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from datetime import datetime, timezone
import asyncio
import re
from discord.ui import Modal, TextInput
from discord.ui import View, Button
from discord import ButtonStyle
from typing import Optional

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

RSN_SHEET_TAB_NAME = "Tracker"
rsn_sheet = sheet_client.open_by_key("1ZwJiuVMp-3p8UH0NCVYTV9_UVI26jl5kWu2nvdspl9k").worksheet("Tracker")


# ---------------------------
# 🔹 Coffer Sheets Setup
# ---------------------------
credentials_dict_coffer = {
  "type": os.getenv('COFFER_TYPE'),
  "project_id": os.getenv('COFFER_ID'),
  "private_key_id": os.getenv('COFFER_PRIVATE_KEY_ID'),
  "private_key": os.getenv('COFFER_PRIVATE_KEY').replace("\\n", "\n"),
  "client_email": os.getenv('COFFER_CLIENT_EMAIL'),
  "client_id": os.getenv('COFFER_CLIENT_ID'),
  "auth_uri": os.getenv('COFFER_AUTH_URI'),
  "token_uri": os.getenv('COFFER_TOKEN_URI'),
  "auth_provider_x509_cert_url": os.getenv('COFFER_AUTH_PROVIDER_X509_CERT_URL'),
  "client_x509_cert_url": os.getenv('COFFER_CLIENT_X509_CERT_URL'),
  "universe_domain": os.getenv('COFFER_UNIVERSE_DOMAIN')
}

coffer_creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict_coffer, scope)
sheet_client_coffer = gspread.authorize(coffer_creds)

coffer_sheet_id = "1dsRSYpDim5zEsldi572L4ljAcMClLyZbUs0HxIinytc"
COFFER_SHEET_TAB_NAME = "Coffer"
coffer_sheet = sheet_client_coffer.open_by_key(coffer_sheet_id).worksheet(COFFER_SHEET_TAB_NAME)

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
REQUIRED_ROLE_NAME = "Event Staff"
REGISTERED_ROLE_NAME = "Registered"
BANK_CHANNEL_ID = 1276197776849633404
CURRENCY_SYMBOL = " 💰"
LISTEN_CHANNEL_ID = 1272875477555482666
COLLAT_CHANNEL_ID = 1272648340940525648

# ---------------------------
# 🔹 Welcome
# ---------------------------

@bot.tree.command(name="welcome", description="Welcome the ticket creator and give them the Recruit role.")
async def welcome(interaction: discord.Interaction):
    # Make sure command is used inside a ticket thread
    if not isinstance(interaction.channel, discord.Thread):
        await interaction.response.send_message("⚠️ This command must be used inside a ticket thread.", ephemeral=True)
        return

    # Find the ticket creator by scanning recent messages from the Tickets bot
    ticket_creator = None
    async for message in interaction.channel.history(limit=20, oldest_first=True):
        if message.author.bot and message.author.name.lower().startswith("tickets"):
            for mention in message.mentions:
                if not mention.bot:
                    ticket_creator = mention
                    break
        if ticket_creator:
            break

    if not ticket_creator:
        await interaction.response.send_message("⚠️ Could not detect who opened this ticket.", ephemeral=True)
        return

    # Assign roles
    guild = interaction.guild
    roles_to_assign = ["Recruit", "Member", "Boss of the Week", "Skill of the Week", "Events"]
    missing_roles = []
    for role_name in roles_to_assign:
        role = discord.utils.get(guild.roles, name=role_name)
        if role:
            await ticket_creator.add_roles(role)
        else:
            missing_roles.append(role_name)

    if missing_roles:
        await interaction.response.send_message(
            f"⚠️ Missing roles: {', '.join(missing_roles)}. Please check the server roles.", ephemeral=True
        )
        return

    # Build and send embed
    embed = discord.Embed(
        title="🎉 Welcome to the Clan! 🎉",
        description=(
            f"Happy to have you with us, {ticket_creator.mention}! 🎊\n\n"
            "📜 Please make sure you visit our [Guidelines]"
            "(https://discord.com/channels/1272629330115297330/1272629843552501802) "
            "to ensure you're aware of the rules.\n\n"
            "**💡 Self-Role Assign**\n"
            "[Click here](https://discord.com/channels/1272629330115297330/1272648586198519818) — "
            "Select roles to be pinged for bosses, raids, and other activities, "
            "including **@Sanguine Sunday** for Theatre of Blood **learner** runs on Sundays. 🩸\n\n"
        ),
        color=discord.Color.blurple()
    )
    
    # Social links - inline
    embed.add_field(
        name="💭 General Chat",
        value="[Say hello!](https://discord.com/channels/1272629330115297330/1272629331524587623)",
        inline=True
    )
    embed.add_field(
        name="✨ Achievements",
        value="[Show off your gains](https://discord.com/channels/1272629330115297330/1272629331524587624)",
        inline=True
    )
    embed.add_field(
        name="💬 Clan Chat",
        value="[Stay updated](https://discord.com/channels/1272629330115297330/1272875477555482666)",
        inline=True
    )
    
    embed.add_field(
        name="🏹 Team Finder",
        value="[Find PVM teams](https://discord.com/channels/1272629330115297330/1272648555772776529)",
        inline=True
    )
    embed.add_field(
        name="📢 Events",
        value="[Check upcoming events](https://discord.com/channels/1272629330115297330/1272646577432825977)",
        inline=True
    )
    embed.add_field(
        name="⚔️ Rank Up",
        value="[Request a rank up](https://discord.com/channels/1272629330115297330/1272648472184487937)\n",
        inline=True
    )
    
    embed.add_field(
        name=" ",
        value=" ",
        inline=True
    )
    
    embed.add_field(
        name="🎓 Mentor Info",
        value="",
        inline=True
    )

    embed.add_field(
        name=" ",
        value=" ",
        inline=True
    )
    
    embed.add_field(
        name=(
            "<:corporal:1273838960367505532> **Want to learn raids?**\n"
            "Once you've been here for two weeks and earned your "
            "<:corporal:1273838960367505532> rank, you can open a mentor ticket "
            "for guidance on PVM!"
        ),
        value="",
        inline=True
    )
    embed.add_field(
        name=(
            "<:mentor:1273838962753929307> **Want to mentor others?**\n"
            "Please open a mentor rank request in <#1272648472184487937>. "
            "State which raid you’d like to mentor and an admin will reach out to you."
        ),
        value="",
        inline=True
    )
    
    embed.add_field(
        name="⚠️ Need Help?",
        value=(
            "If you encounter any issues, please reach out to Clan Staff or use the "
            "[Support Ticket channel](https://discord.com/channels/1272629330115297330/1272648498554077304)."
        ),
        inline=False
    )

    await interaction.response.send_message(embed=embed)

ROLE_PANEL_CHANNEL_ID = 1234567890  # replace with your channel ID

# -----------------------------
# Role Button
# -----------------------------
class RoleButton(Button):
    def __init__(self, role_name: str, emoji=None):
        super().__init__(label=role_name, style=discord.ButtonStyle.secondary, emoji=emoji, custom_id=role_name)

    async def callback(self, interaction: discord.Interaction):
        role_name = self.custom_id
        role = discord.utils.get(interaction.guild.roles, name=role_name)

        if not role:
            await interaction.response.send_message(f"❌ Role '{role_name}' not found.", ephemeral=True)
            return

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            feedback = f"{interaction.user.mention}, role **{role_name}** removed."
        else:
            await interaction.user.add_roles(role)
            feedback = f"{interaction.user.mention}, role **{role_name}** added."

        await interaction.response.send_message(feedback, ephemeral=False)
        await asyncio.sleep(1)
        try:
            await interaction.delete_original_response()
        except Exception:
            pass

# -----------------------------
# Views for each group
# -----------------------------
class RaidsView(View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=None)
        get_emoji = lambda name: discord.utils.get(guild.emojis, name=name)

        self.add_item(RoleButton("Theatre of Blood", get_emoji("tob")))
        self.add_item(RoleButton("Chambers of Xeric", get_emoji("cox")))
        self.add_item(RoleButton("Tombs of Amascut", get_emoji("toa")))
        self.add_item(RoleButton("Theatre of Blood Hard Mode", get_emoji("hmt")))
        self.add_item(RoleButton("Chambers of Xeric Challenge Mode", get_emoji("cm")))
        self.add_item(RoleButton("Tombs of Amascut Expert", get_emoji("extoa")))


class BossesView(View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=None)
        get_emoji = lambda name: discord.utils.get(guild.emojis, name=name)

        self.add_item(RoleButton("Bandos GWD", get_emoji("graardor")))
        self.add_item(RoleButton("Saradomin GWD", get_emoji("sara")))
        self.add_item(RoleButton("Zamorak GWD", get_emoji("zammy")))
        self.add_item(RoleButton("Armadyl GWD", get_emoji("arma")))
        self.add_item(RoleButton("Nex", get_emoji("nex")))
        self.add_item(RoleButton("Corporeal Beast", get_emoji("corp")))
        self.add_item(RoleButton("Callisto", get_emoji("callisto")))
        self.add_item(RoleButton("Vet'ion", get_emoji("vetion")))
        self.add_item(RoleButton("Venenatis", get_emoji("venenatis")))
        self.add_item(RoleButton("Hueycoatl", get_emoji("hueycoatl")))
        self.add_item(RoleButton("Yama", get_emoji("yama")))

class EventsView(View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=None)
        get_emoji = lambda name: discord.utils.get(guild.emojis, name=name)

        self.add_item(RoleButton("Raffles", get_emoji("raffle")))
        self.add_item(RoleButton("Events", get_emoji("event")))
        self.add_item(RoleButton("Boss of the Week", get_emoji("botw")))
        self.add_item(RoleButton("Skill of the Week", get_emoji("sotw")))
        self.add_item(RoleButton("Sanguine Sunday - Learn ToB!", get_emoji("sanguine_sunday")))


# ---------------------------
# 🔹 RSN Commands
# ---------------------------

rsn_write_queue = asyncio.Queue()

async def rsn_writer():
    while True:
        member: discord.Member
        rsn_value: str
        member, rsn_value = await rsn_write_queue.get()
        try:
            cell = rsn_sheet.find(str(member.id))
            now = datetime.now(timezone.utc)
            day = now.day  # integer day
            timestamp = now.strftime(f"%B {day}, %Y at %I:%M%p")
            if cell is not None:
                # Get old RSN before overwriting
                old_rsn = rsn_sheet.cell(cell.row, 4).value or ""
                rsn_sheet.update_cell(cell.row, 4, rsn_value)
                rsn_sheet.update_cell(cell.row, 5, timestamp)
                print(f"✅ Updated RSN for {member} ({member.id}) to {rsn_value}")
            else:
                old_rsn = ""
                rsn_sheet.append_row([
                    member.display_name,
                    str(member.id),
                    old_rsn,
                    rsn_value,
                    timestamp
                ])
                print(f"✅ Added new RSN for {member} ({member.id}) as {rsn_value}")
        except Exception as e:
            print(f"Error writing RSN to sheet: {e}")
        rsn_write_queue.task_done()


class RSNModal(discord.ui.Modal, title="Register your RuneScape Name"):
    rsn = discord.ui.TextInput(
        label="Enter your RuneScape Name 🧙",
        placeholder="e.g. Zezima",
        required=True,
        max_length=12
    )

    async def on_submit(self, modal_interaction: discord.Interaction):
        member = modal_interaction.user
        rsn_value = self.rsn.value

        now = datetime.now(timezone.utc)
        day = now.day
        timestamp = now.strftime(f"%B {day}, %Y at %I:%M%p")

        try:
            cell = rsn_sheet.find(str(member.id))
            if cell:
                # Get current "New RSN"
                old_rsn = rsn_sheet.cell(cell.row, 4).value or ""
                # Move it into "Old RSN"
                rsn_sheet.update_cell(cell.row, 3, old_rsn)
                # Update New RSN + Date/Time
                rsn_sheet.update_cell(cell.row, 4, rsn_value)
                rsn_sheet.update_cell(cell.row, 5, timestamp)
                print(f"✅ Updated RSN for {member} ({member.id}) to {rsn_value}")
            else:
                # New entry
                rsn_sheet.append_row([
                    member.display_name,
                    str(member.id),
                    "",
                    rsn_value,
                    timestamp
                ])
                print(f"✅ Added new RSN for {member} ({member.id}) as {rsn_value}")
        except Exception as e:
            print(f"❌ Error writing RSN: {e}")

        # Add Registered role if not already
        guild = modal_interaction.guild
        if guild:
            registered_role = discord.utils.get(guild.roles, name=REGISTERED_ROLE_NAME)
            if registered_role and registered_role not in member.roles:
                await member.add_roles(registered_role, reason="Registered RSN")

        await modal_interaction.response.send_message(
            f"✅ Your RuneScape name has been submitted as **{rsn_value}**.",
            ephemeral=True
        )

class RSNPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view: no timeout

    @discord.ui.button(
        label="Register RSN",
        style=discord.ButtonStyle.success,
        emoji="📝",
        custom_id="register_rsn_button"
    )
    async def register_rsn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RSNModal())


@tree.command(name="rsn_panel", description="Open the RSN registration panel.")
@app_commands.checks.has_any_role("Moderators")
async def rsn_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="<:1gp:1347684047773499482> Register your RuneScape Name",
        description=(
            "Click the button below to register or update your RuneScape name in the clan records.\n\n"
            "This helps event staff verify drops and track your achievements. 🪙"
        ),
        color=discord.Color.green()
    )

    await interaction.response.send_message(
        embed=embed,
        view=RSNPanelView(),
        ephemeral=False
    )


@tree.command(name="rsn", description="Check your registered RSN.")
async def rsn(interaction: discord.Interaction):
    member_id = str(interaction.user.id)

    try:
        cell = rsn_sheet.find(member_id)
        rsn_value = rsn_sheet.cell(cell.row, 4).value
        await interaction.response.send_message(
            f"✅ Your registered RSN is **{rsn_value}**.",
            ephemeral=True
        )
    except gspread.exceptions.CellNotFound:
        await interaction.response.send_message(
            "⚠️ You have not registered an RSN yet. Use `/rsn_panel` to register.",
            ephemeral=True
        )

@rsn_panel.error
async def rsn_panel_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingAnyRole):
        await interaction.response.send_message(
            "⛔ You do not have permission to use this command.",
            ephemeral=True
        )


# ---------------------------
# 🔹 TimeZones
# ---------------------------

class TimePanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Morning (8AM–12PM)", style=discord.ButtonStyle.primary, custom_id="time_morning"))
        self.add_item(Button(label="Afternoon (12PM–4PM)", style=discord.ButtonStyle.primary, custom_id="time_afternoon"))
        self.add_item(Button(label="Evening (4PM–10PM)", style=discord.ButtonStyle.primary, custom_id="time_evening"))
        self.add_item(Button(label="Late Night (10PM–2AM)", style=discord.ButtonStyle.primary, custom_id="time_latenight"))


# Timezones and flags
TIMEZONE_DATA = {
    "PST": ("America/Los_Angeles", "🇺🇸"),
    "MST": ("America/Denver", "🇺🇸"),
    "CST": ("America/Chicago", "🇺🇸"),
    "EST": ("America/New_York", "🇺🇸"),
    "AST": ("America/Halifax", "🇨🇦"),
    "BRT": ("Brazil", "🇧🇷"),
    "ART": ("Argentina", "🇦🇷"),
    "GMT": ("Europe/London", "🇬🇧"),
    "CET": ("Europe/Paris", "🇫🇷"),
    "EET": ("Europe/Helsinki", "🇫🇮"),
    "AWST": ("Australia/Perth", "🇦🇺"),
    "ACST": ("Australia/Adelaide", "🇦🇺"),
    "AEST": ("Australia/Sydney", "🇦🇺"),
}

TIME_OF_DAY_DATA = {
    "Morning": ("🌄", "6 AM - 12 PM"),
    "Day": ("🌇", "12 PM - 6 PM"),
    "Evening": ("🌆", "6 PM - 12 AM"),
    "Night": ("🌃", "12 AM - 6 AM"),
}

class TimeOfDayView(discord.ui.View):
    def __init__(self, guild, timezone_role, tz_abbr):
        super().__init__(timeout=60)
        self.guild = guild
        self.timezone_role = timezone_role
        self.tz_abbr = tz_abbr

        for tod_label, (emoji, _) in TIME_OF_DAY_DATA.items():
            role = discord.utils.get(guild.roles, name=tod_label)
            if role:
                self.add_item(TimeOfDayButton(tod_label, role, emoji, self.timezone_role, self.tz_abbr))

class TimeOfDayButton(discord.ui.Button):
    def __init__(self, label, role, emoji, timezone_role, tz_abbr):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, emoji=emoji)
        self.role = role
        self.label = label
        self.timezone_role = timezone_role
        self.tz_abbr = tz_abbr

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user

        if self.role in member.roles:
            await member.remove_roles(self.role)
            await interaction.response.send_message(
                f"❌ Removed time of day role **{self.label}**.",
                ephemeral=True
            )
            return

        await member.add_roles(self.role)
        time_range = TIME_OF_DAY_DATA[self.label][1]
        await interaction.response.send_message(
            f"✅ Added time of day role **{self.label}** ({time_range}) for timezone **{self.tz_abbr}**.",
            ephemeral=True
        )

class TimezoneView(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=None)
        self.guild = guild
        for tz_abbr, (tz_str, flag) in TIMEZONE_DATA.items():
            role = discord.utils.get(guild.roles, name=tz_abbr)
            if role:
                self.add_item(TimezoneButton(tz_abbr, role, tz_str, flag, guild))

class TimezoneButton(discord.ui.Button):
    def __init__(self, tz_abbr, role, tz_str, emoji, guild):
        custom_id = f"timezone-btn:{role.id}"
        super().__init__(label=tz_abbr, style=discord.ButtonStyle.primary, custom_id=custom_id, emoji=emoji)
        self.tz_abbr = tz_abbr
        self.role = role
        self.tz_str = tz_str
        self.guild = guild

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        guild = interaction.guild

        if self.role in member.roles:
            await member.remove_roles(self.role)
            await interaction.response.send_message(
                f"❌ Removed timezone role **{self.tz_abbr}**.",
                ephemeral=True
            )
            return

        old_tz_roles = [discord.utils.get(guild.roles, name=abbr) for abbr in TIMEZONE_DATA.keys()]
        old_tz_roles = [r for r in old_tz_roles if r and r in member.roles]
        if old_tz_roles:
            await member.remove_roles(*old_tz_roles)

        await member.add_roles(self.role)

        await interaction.response.send_message(
            f"✅ Timezone set to **{self.tz_abbr}**. Now select your usual time of day:",
            view=TimeOfDayView(guild, self.role, self.tz_abbr),
            ephemeral=True,
        )

@bot.tree.command(name="time_panel", description="Open the timezone selection panel.")
async def time_panel(interaction: discord.Interaction):
    view = TimezoneView(interaction.guild)
    embed = discord.Embed(
        title="🕒 Select Your Usual Timezones",
        description=(
            "Click the button that best matches the **timezones you are most often playing or active**.\n\n"
            "After selecting, you’ll get another prompt to pick the **time of day** you usually play."
        ),
        color=discord.Color.blurple()
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


from datetime import datetime
import discord
from discord import app_commands
from discord.ui import Modal, TextInput

# ---------------------------
# 🔹 Coffer
# ---------------------------

CUSTOM_EMOJI = "<:MaxCash:1347684049040183427>"

def parse_amount(input_str: str) -> int:
    """
    Parse input like '20m', '20 m', '1.5m', '1,5m' as millions.
    Also accept plain integers like '5000' (which are treated as millions).
    Returns integer amount in full units (e.g. 1,500,000).
    """
    input_str = input_str.lower().replace(" ", "").replace(",", ".")
    if input_str.endswith("m"):
        try:
            number_part = float(input_str[:-1])
            return int(number_part * 1_000_000)
        except ValueError:
            raise ValueError("Invalid amount format")
    else:
        # treat raw numbers as millions as before (float to support decimals)
        try:
            number_part = float(input_str)
            return int(number_part * 1_000_000)
        except ValueError:
            raise ValueError("Invalid amount format")


def format_million(amount: int) -> str:
    millions = amount / 1_000_000
    if millions.is_integer():
        return f"{int(millions):,}M"
    else:
        return f"{millions:,.2f}M".rstrip('0').rstrip('.')


def log_coffer_entry(name: str, amount: int, entry_type: str, coffer_change: int = 0):
    timestamp = datetime.now().strftime("%I:%M%p %m/%d/%Y").lstrip("0").replace(" 0", " ")
    coffer_sheet.append_row([
        name,
        amount,
        entry_type,
        f"{'+' if coffer_change >= 0 else ''}{coffer_change}",
        timestamp
    ])


def get_current_total_and_holders_and_owed():
    records = coffer_sheet.get_all_records()
    total = 0
    inferred_holders = {}
    inferred_owed = {}

    for row in records:
        name = row.get("Name")
        amount = int(row.get("Amount", 0))
        entry_type = row.get("Type", "").lower()

        if entry_type == "deposit":
            total += amount
            inferred_holders[name] = inferred_holders.get(name, 0) + amount
        elif entry_type == "withdraw":
            total -= amount
            inferred_holders[name] = inferred_holders.get(name, 0) - amount

    # Apply any latest 'holding' and 'owed' overrides
    for row in records:
        name = row.get("Name")
        amount = int(row.get("Amount", 0))
        entry_type = row.get("Type", "").lower()

        if entry_type == "holding":
            inferred_holders[name] = amount
        elif entry_type == "owed":
            inferred_owed[name] = amount

    # Remove zero or negative amounts
    holders = {k: v for k, v in inferred_holders.items() if v > 0}
    owed = {k: v for k, v in inferred_owed.items() if v > 0}

    return total, holders, owed


def escape_markdown(text: str) -> str:
    # Escape all Discord markdown special characters to avoid formatting issues
    # From Discord docs: \* _ ~ ` > | (and some others)
    to_escape = r"\*_~`>|"
    return re.sub(f"([{re.escape(to_escape)}])", r"\\\1", text)


# ---------------------------
# 🔹 Discord Modals and Commands
# ---------------------------

class DepositWithdrawModal(Modal, title="Deposit/Withdraw"):
    amount_input = TextInput(label="Amount", placeholder="Enter amount (e.g. 20m)", required=True)

    def __init__(self, action: str):
        super().__init__()
        self.action = action

    async def on_submit(self, interaction: discord.Interaction):
        raw_value = self.amount_input.value
        try:
            amount = parse_amount(raw_value)
        except Exception:
            await interaction.response.send_message(
                "❌ Invalid amount format. Use numbers or numbers with 'm' (e.g. 20m).",
                ephemeral=True
            )
            return

        name = interaction.user.display_name

        total, holders, owed = get_current_total_and_holders_and_owed()
        current_holding = holders.get(name, 0)

        if self.action == "Deposit":
            log_coffer_entry(name, amount, "deposit", amount)

            # Adjust holding if user already holds money
            if current_holding > 0:
                new_holding = max(current_holding - amount, 0)
            else:
                new_holding = 0  # no holdings previously

            log_coffer_entry(name, new_holding, "holding", 0)

            verb = "deposited"
            formatted_amount = format_million(amount)

            await interaction.response.send_message(
                f"{CUSTOM_EMOJI} {name} {verb} {formatted_amount}!",
                ephemeral=False
            )

        else:  # Withdraw
            log_coffer_entry(name, amount, "withdraw", -amount)

            # Holdings not changed on withdraw here

            verb = "withdrew"
            formatted_amount = format_million(amount)

            await interaction.response.send_message(
                f"{CUSTOM_EMOJI} {name} {verb} {formatted_amount}!",
                ephemeral=False
            )


class HoldingModal(Modal, title="Set Holding Amount"):
    amount_input = TextInput(label="Amount Held", placeholder="Enter amount held (e.g. 20m)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        raw_value = self.amount_input.value
        try:
            amount = parse_amount(raw_value)
        except Exception:
            await interaction.response.send_message(
                "❌ Invalid amount format. Use numbers or numbers with 'm' (e.g. 20m).",
                ephemeral=True
            )
            return

        name = interaction.user.display_name

        if amount > 0:
            log_coffer_entry(name, amount, "holding", 0)
            formatted_amount = format_million(amount)
            await interaction.response.send_message(
                f"{CUSTOM_EMOJI} {name} is now holding {formatted_amount}.",
                ephemeral=False
            )
        else:
            log_coffer_entry(name, 0, "holding", 0)
            await interaction.response.send_message(
                f"{CUSTOM_EMOJI} {name} is no longer holding any money.",
                ephemeral=False
            )


@bot.tree.command(name="deposit", description="Deposit money into the clan coffer")
async def deposit(interaction: discord.Interaction):
    await interaction.response.send_modal(DepositWithdrawModal("Deposit"))


@bot.tree.command(name="withdraw", description="Withdraw money from the clan coffer")
async def withdraw(interaction: discord.Interaction):
    await interaction.response.send_modal(DepositWithdrawModal("Withdraw"))


@bot.tree.command(name="holding", description="Add to a user's holding amount (defaults to yourself)")
@app_commands.describe(
    user="User to add holding for (default yourself)",
    amount="Amount to add (e.g. 20m)"
)
async def holding(
    interaction: discord.Interaction,
    amount: str,
    user: discord.User | None = None
):
    target = user or interaction.user
    name = target.display_name

    try:
        amt = parse_amount(amount)
    except Exception:
        await interaction.response.send_message(
            "❌ Invalid amount format. Use numbers or numbers with 'm' (e.g. 20m).",
            ephemeral=True
        )
        return

    # Get current holdings
    _, holders, _ = get_current_total_and_holders_and_owed()
    current_amt = holders.get(name, 0)

    # Add entered amount to current
    new_amt = current_amt + amt

    if new_amt > 0:
        log_coffer_entry(name, new_amt, "holding", amt)
        await interaction.response.send_message(
            f"{CUSTOM_EMOJI} **{name}** is now holding {format_million(new_amt)}.",
            ephemeral=False
        )
    else:
        log_coffer_entry(name, 0, "holding", -current_amt)
        await interaction.response.send_message(
            f"{CUSTOM_EMOJI} **{name}** is no longer holding any money.",
            ephemeral=False
        )


@bot.tree.command(name="owed", description="Set a user's owed amount (defaults to yourself)")
@app_commands.describe(
    user="User to set owed amount for (default yourself)",
    amount="Amount owed (e.g. 20m)"
)
async def owed(
    interaction: discord.Interaction,
    amount: str,
    user: discord.User | None = None
):
    target = user or interaction.user
    name = target.display_name

    try:
        amt = parse_amount(amount)
    except Exception:
        await interaction.response.send_message(
            "❌ Invalid amount format. Use numbers or numbers with 'm' (e.g. 20m).",
            ephemeral=True
        )
        return

    if amt > 0:
        log_coffer_entry(name, amt, "owed", 0)
        formatted_amount = format_million(amt)
        await interaction.response.send_message(
            f"{CUSTOM_EMOJI} {name} is now owed {formatted_amount}.",
            ephemeral=False
        )
    else:
        log_coffer_entry(name, 0, "owed", 0)
        await interaction.response.send_message(
            f"{CUSTOM_EMOJI} {name} is no longer owed any money.",
            ephemeral=False
        )

@bot.tree.command(name="clear_owed", description="Clear owed amount for a user")
@app_commands.describe(user="User to clear owed amount for")
async def clear_owed(interaction: discord.Interaction, user: discord.User):
    name = user.display_name

    log_coffer_entry(name, 0, "owed", 0)

    await interaction.response.send_message(
        f"{CUSTOM_EMOJI} Cleared owed amount for **{name}**.",
        ephemeral=False
    )

@bot.tree.command(name="clear_holding", description="Clear holding amount for a user")
@app_commands.describe(user="User to clear holding for")
async def clear_holding(interaction: discord.Interaction, user: discord.User):
    name = user.display_name

    log_coffer_entry(name, 0, "holding", 0)

    await interaction.response.send_message(
        f"{CUSTOM_EMOJI} Cleared holding for **{name}**.",
        ephemeral=False
    )

@bot.tree.command(name="bank", description="Show coffer total and who is holding or owed money")
async def bank(interaction: discord.Interaction):
    total, holders, owed = get_current_total_and_holders_and_owed()
    guild = interaction.guild

    # Sum all holdings to add to the clan coffer total
    total_holding = sum(holders.values())
    clan_coffer_total = total + total_holding

    filtered_holders = {name: amount for name, amount in holders.items() if amount > 0}
    filtered_owed = {name: amount for name, amount in owed.items() if amount > 0}

    holder_lines = []
    for name, amount in filtered_holders.items():
        member = discord.utils.get(guild.members, display_name=name) or discord.utils.get(guild.members, name=name)
        display_name = member.nick if member and member.nick else name
        display_name = escape_markdown(display_name)
        formatted_amount = f"{CUSTOM_EMOJI} {format_million(amount)}"
        holder_lines.append(f"🏦 **{display_name}** is holding {formatted_amount}")

    owed_lines = []
    for name, amount in filtered_owed.items():
        member = discord.utils.get(guild.members, display_name=name) or discord.utils.get(guild.members, name=name)
        display_name = member.nick if member and member.nick else name
        display_name = escape_markdown(display_name)
        formatted_amount = f"{CUSTOM_EMOJI} {format_million(amount)}"
        owed_lines.append(f"💰 **{display_name}** is owed {formatted_amount}")

    ceo_bank_line = f"{CUSTOM_EMOJI} CEO Bank: {format_million(total)}"
    clan_coffer_line = f"💰 Clan Coffer Total: {format_million(clan_coffer_total)}"

    holder_text = "\n".join(holder_lines) if holder_lines else "_Nobody is holding anything._"
    owed_text = "\n".join(owed_lines) if owed_lines else "_Nobody is owed anything._"

    await interaction.response.send_message(
        f"**{ceo_bank_line}**\n**{clan_coffer_line}**\n\n{holder_text}\n\n{owed_text}",
        ephemeral=False
    )

# ---------------------------
# 🔹 Panel Init()
# ---------------------------

async def send_rsn_panel(channel: discord.TextChannel):
    await channel.purge(limit=10)
    await channel.send(":identification_card: **Link your RSN by clicking below:**", view=RSNPanelView())

async def send_time_panel(channel: discord.TextChannel):
    await channel.purge(limit=10)
    # Fix here: Send the embed + TimezoneView like the command does, NOT the old TimePanelView buttons
    view = TimezoneView(channel.guild)
    embed = discord.Embed(
        title="🕒 Select Your Usual Timezones",
        description=(
            "Click the button that best matches the **timezones you are most often playing or active**.\n\n"
            "After selecting, you’ll get another prompt to pick the **time of day** you usually play."
        ),
        color=discord.Color.blurple()
    )
    await channel.send(embed=embed, view=view)

async def send_role_panel(channel: discord.TextChannel):
    await channel.purge(limit=10)
    await channel.send(":crossed_swords: **Choose your roles:**", view=RolePanelView(channel.guild))

# ---------------------------
# 🔹 Collat Notifier
# ---------------------------

class CollatRequestModal(discord.ui.Modal, title="Request Item"):
    target_username = discord.ui.TextInput(
        label="Enter the username to notify",
        placeholder="Exact username (case-sensitive)",
        style=discord.TextStyle.short,
        required=True,
        max_length=50,
    )

    def __init__(self, interaction: discord.Interaction):
        super().__init__()
        self.interaction = interaction  # who clicked the button

    async def on_submit(self, interaction: discord.Interaction):
        entered_name = str(self.target_username.value).strip()

        # Try to find the member in the guild
        guild = interaction.guild
        target_member = discord.utils.find(
            lambda m: m.name == entered_name or m.display_name == entered_name,
            guild.members
        )

        if not target_member:
            await interaction.response.send_message(
                "User not found. Please ensure the name matches exactly.",
                ephemeral=True
            )
            return

        # Post reply under the original collat message with proper mentions
        await interaction.message.reply(
            f"{self.interaction.user.mention} is requesting their item from {target_member.mention}",
            mention_author=True,
        )

        await interaction.response.send_message("Request sent ✅", ephemeral=True)

class CollatButtons(discord.ui.View):
    def __init__(self, author: discord.User, mentioned: discord.User | None):
        super().__init__(timeout=None)
        self.author = author
        self.mentioned = mentioned
        self.disabled_flag = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Restrict usage to only the author or mentioned user
        if interaction.user == self.author or (self.mentioned and interaction.user == self.mentioned):
            return True
        await interaction.response.send_message("You are not allowed to interact with this post.", ephemeral=True)
        return False

    async def disable_all(self, interaction: discord.Interaction):
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

    @discord.ui.button(label="Request Item", style=discord.ButtonStyle.primary, emoji="🔔")
    async def request_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.mentioned:
            # Open modal instead of error
            await interaction.response.send_modal(CollatRequestModal(interaction))
            return

        # Determine who to ping
        if interaction.user == self.author:
            target = self.mentioned
        else:
            target = self.author

        await interaction.response.defer()
        await interaction.message.reply(
            f"{interaction.user.mention} is requesting their item from {target.mention}.",
            mention_author=True
        )

    @discord.ui.button(label="Item Returned", style=discord.ButtonStyle.success, emoji="📥")
    async def item_returned(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable all buttons after this
        await self.disable_all(interaction)
        await interaction.response.send_message("Item marked as returned. ✅", ephemeral=True)


@bot.event
async def on_message(message: discord.Message):
    # Only in collat channel
    if message.channel.id != COLLAT_CHANNEL_ID:
        return
    if message.author.bot:
        return
    if not message.attachments:  # Require screenshot
        return

    # Detect first mentioned user in the message
    mentioned_user = message.mentions[0] if message.mentions else None

    # Add buttons
    view = CollatButtons(message.author, mentioned_user)
    await message.reply("Collat actions:", view=view)

# ---------------------------
# 🔹 Bot Events
# ---------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.wait_until_ready()

    # ---------------------------
    # RSN panel → Channel ID: 1280532494139002912
    # ---------------------------
    rsn_channel = bot.get_channel(1280532494139002912)
    if rsn_channel:
        await send_rsn_panel(rsn_channel)

    # ---------------------------
    # Time panel → Channel ID: 1398775387139342386
    # ---------------------------
    time_channel = bot.get_channel(1398775387139342386)
    if time_channel:
        await send_time_panel(time_channel)

    # ---------------------------
    # Role panel → Channel ID: 1272648586198519818
    # ---------------------------
    role_channel = bot.get_channel(1272648586198519818)
    if role_channel:
        guild = role_channel.guild

        # Delete old role panel messages
        async for msg in role_channel.history(limit=100):
            if msg.author == bot.user:
                await msg.delete()

        # Intro message
        await role_channel.send("Select your roles below:")

        # Post each panel as an embed + buttons
        raid_embed = discord.Embed(title="⚔︎ ℜ𝔞𝔦𝔡𝔰 ⚔︎", description="", color=0x00ff00)
        await role_channel.send(embed=raid_embed, view=RaidsView(guild))

        boss_embed = discord.Embed(title="⚔︎ 𝔊𝔯𝔬𝔲𝔭 𝔅𝔬𝔰𝔰𝔢𝔰 ⚔︎", description="", color=0x0000ff)
        await role_channel.send(embed=boss_embed, view=BossesView(guild))

        events_embed = discord.Embed(title="⚔︎ 𝔈𝔳𝔢𝔫𝔱𝔰 ⚔︎", description="", color=0xffff00)
        await role_channel.send(embed=events_embed, view=EventsView(guild))

    # ---------------------------
    # Optional: Sync commands
    # ---------------------------
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Command sync failed: {e}")

bot.run(os.getenv('DISCORD_BOT_TOKEN'))
