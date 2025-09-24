import os
import discord
from discord.ext import commands
from discord import app_commands
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import asyncio
import re
from discord.ui import Modal, TextInput
from discord.ui import View, Button
from discord import ButtonStyle
from typing import Optional
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from gspread.exceptions import APIError, GSpreadException

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
BANK_CHANNEL_ID = 1276197776849633404
CURRENCY_SYMBOL = " 💰"
LISTEN_CHANNEL_ID = 1272875477555482666
COLLAT_CHANNEL_ID = 1272648340940525648

WATCH_CHANNEL_IDS = [
    1272648453264248852,
    1272648472184487937
]

STAFF_ROLE_ID = 1272635396991221824

# ---------------------------
# 🔹 Ticket Scores Setup
# ---------------------------

TICKET_SCORES_TAB_NAME = "TicketScores"
ticket_scores_sheet = sheet_client_coffer.open_by_key(coffer_sheet_id).worksheet(TICKET_SCORES_TAB_NAME)

def get_or_create_mod_row(mod_name: str):
    """Find moderator row or create it if missing."""
    try:
        cell = ticket_scores_sheet.find(mod_name)
        if cell:
            return cell.row
    except Exception:
        pass

    ticket_scores_sheet.append_row([mod_name, "0", "0", "0"])
    cell = ticket_scores_sheet.find(mod_name)
    return cell.row

def increment_ticket_score(mod_name: str):
    """Increment scores for moderator across Overall, Weekly, and Monthly."""
    row = get_or_create_mod_row(mod_name)
    values = ticket_scores_sheet.row_values(row)

    while len(values) < 4:
        values.append("0")

    overall = int(values[1]) + 1
    weekly = int(values[2]) + 1
    monthly = int(values[3]) + 1

    ticket_scores_sheet.update(f"B{row}:D{row}", [[overall, weekly, monthly]])

@bot.tree.command(name="ticketscore", description="Show ticket and message scores (weekly, monthly, overall).")
async def ticketscore(interaction: discord.Interaction):
    guild = interaction.guild
    staff_role = discord.utils.get(guild.roles, name="Clan Staff")
    if not staff_role or staff_role not in interaction.user.roles:
        await interaction.response.send_message(
            "⚠️ You do not have permission to view ticket scores.", ephemeral=True
        )
        return

    loop = asyncio.get_running_loop()

    def fetch_scores(sheet):
        rows = sheet.get_all_values()[1:]
        scores = []
        for row in rows:
            if len(row) >= 4:
                name = row[0]
                try:
                    overall = int(row[1])
                    monthly = int(row[2])
                    weekly = int(row[3])
                except ValueError:
                    overall, monthly, weekly = 0, 0, 0
                member = guild.get_member_named(name) or guild.get_member(int(name.split("/")[0])) if "/" in name else None
                display_name = member.display_name if member else name
                scores.append((display_name, overall, monthly, weekly))
        return sorted(scores, key=lambda x: x[1], reverse=True)

    ticket_scores = await loop.run_in_executor(None, fetch_scores, ticket_scores_sheet)
    message_scores = await loop.run_in_executor(None, fetch_scores, message_scores_sheet)

    embed = discord.Embed(
        title="🎟️ Ticket & Message Scores",
        description="Weekly resets every Monday • Monthly resets on the 1st",
        color=discord.Color.gold()
    )

    if ticket_scores:
        ticket_table = "\n".join(
            [f"**{i+1}. {name}** — 👋 {overall} | 🗓️ {monthly} | 📆 {weekly}"
             for i, (name, overall, monthly, weekly) in enumerate(ticket_scores)]
        )
    else:
        ticket_table = "No ticket scores recorded yet."
    embed.add_field(
        name="🎫 /Welcome Commands Used - Total, Month, Week",
        value=ticket_table,
        inline=False
    )

    if message_scores:
        message_table = "\n".join(
            [f"**{i+1}. {name}** — ✉️ {overall} | 🗓️ {monthly} | 📆 {weekly}"
             for i, (name, overall, monthly, weekly) in enumerate(message_scores)]
        )
    else:
        message_table = "No message scores recorded yet."
    embed.add_field(
        name="✉️ Messages In Tickets - Total, Month, Week",
        value=message_table,
        inline=False
    )

    await interaction.response.send_message(embed=embed)

# ---------------------------
# 🔹 Reset Loop
# ---------------------------

@tasks.loop(hours=24)
async def reset_scores():
    today = datetime.utcnow()
    all_values = ticket_scores_sheet.get_all_values()

    if today.weekday() == 0:
        for i in range(2, len(all_values) + 1):
            ticket_scores_sheet.update_cell(i, 3, 0)

    if today.day == 1:
        for i in range(2, len(all_values) + 1):
            ticket_scores_sheet.update_cell(i, 4, 0)

@reset_scores.before_loop
async def before_reset():
    await bot.wait_until_ready()

MODERATOR_ROLE_ID = 1272961765034164318

@app_commands.command(name="rules", description="Post the clan rules message.")
async def rules(interaction: discord.Interaction):
    # check if the user has the moderator role
    if MODERATOR_ROLE_ID not in [role.id for role in interaction.user.roles]:
        await interaction.response.send_message(
            "❌ You don’t have permission to use this command.",
            ephemeral=True
        )
        return

    embed1 = discord.Embed(
        title="Rancour PvM: General Information",
        description="Discord is a clan requirement. We use it for announcements, events, clan discussions, and much more.",
        color=discord.Color.red()
    )
    embed1.add_field(
        name="📢 Announcements",
        value="Please do NOT mute the `📌⎮announcements` channel. We'll do our best to minimise the pings, but this is for important information you might need as a member of the community.",
        inline=False
    )
    embed1.add_field(
        name="💬 Clan Chat and Home Worlds",
        value="**Clan chat:** `Rancour PvM`\n**USA Home world:** `World 494`\n**UK / EU Home world:** `World 514`",
        inline=False
    )

    embed2 = discord.Embed(
        title="📜 The #1 Rule - Respect Others",
        description=(
            "We have a couple of different rules, but our most important one is respect. \n\n"
            "If you follow this one rule and respect others within the clan you will always be welcome with us.\n\n"
            "✦︎ Jagex rules must be followed at all times.\n"
            "✦︎ Set a positive example within the community.\n"
            "✦︎ Be respectful and supportive to all.\n"
            "✦︎ No discrimination, hate speech or bullying of any kind.\n"
            "✦︎ No disruptive or toxic behaviour within Discord or Clan Chat.\n"
            "✦︎ No NSFW content is allowed in the Discord.\n"
            "✦︎ No scamming, luring or belittling.\n"
            "✦︎ No begging / asking for donations.\n"
            "✦︎ Raise any and all issues or concerns with the Clan Staff.\n"
            "✦︎ All loot must be split on PvM trips, unless stated otherwise at the start of the trip.\n"
            "✦︎ **ALL Iron Accounts** must communicate that they are going to split loot unless their team agrees to FFA, this includes FFA worlds and Rare and Mega Rare items!\n"
            "✦︎ Adhere to Discord’s own terms of service and community guidelines.\n"
            "✦︎ Do NOT share other peoples personal information without their consent."
        ),
        color=discord.Color.red()
    )

    embed3 = discord.Embed(
        title="⚙️ Clan Systems & Procedures",
        color=discord.Color.red()
    )
    embed3.add_field(
        name="⚖️ The 3-Strike System",
        value=(
            "The community uses a 3 strike system. The only exception is if someone's conduct is so outrageous that it requires immediate action.\n"
            "• **1st offence** - May result in a recorded warning.\n"
            "• **2nd offence** - May result in another warning and a time out.\n"
            "• **3rd offence** - Will result in removal from the clan.\n\n"
            "*You can appeal a ban or a warning by contacting a Moderator.*"
        ),
        inline=False
    )
    embed3.add_field(
        name="🎟️ The Clan Ticket System",
        value=(
            "If you wish to become a member, rank up, or submit a support ticket, you must use the following channels:\n"
            "• Become a member: `👉⎮become-a-member`\n"
            "• Rank up request: `🍌⎮rank-up`\n"
            "• Support ticket: `🔔⎮support-ticket`\n"
            "• Register your RSN: `🔑⎮rsn-registration`"
        ),
        inline=False
    )
    embed3.add_field(
        name="👋 Guesting in the clan",
        value="Any member of the clan is free to invite their friends to the Discord, even if that person doesn't want to join. Guests can access parts of our server but not everything. When joining, friends will need to request the role of guest from clan staff.",
        inline=False
    )

    await interaction.response.send_message(
        content="https://discord.gg/rancour-pvm",
        embeds=[embed1, embed2, embed3]
    )

# ---------------------------
# 🔹 Welcome
# ---------------------------

@bot.tree.command(name="welcome", description="Welcome the ticket creator and give them the Recruit role.")
async def welcome(interaction: discord.Interaction):
    if not isinstance(interaction.channel, discord.Thread):
        await interaction.response.send_message(
            "⚠️ This command must be used inside a ticket thread.", ephemeral=True
        )
        return

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
        await interaction.response.send_message(
            "⚠️ Could not detect who opened this ticket.", ephemeral=True
        )
        return

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
            f"⚠️ Missing roles: {', '.join(missing_roles)}. Please check the server roles.",
            ephemeral=True
        )
        return

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

    embed.add_field(name="💭 General Chat", value="[Say hello!](https://discord.com/channels/1272629330115297330/1272629331524587623)", inline=True)
    embed.add_field(name="✨ Achievements", value="[Show off your gains](https://discord.com/channels/1272629330115297330/1272629331524587624)", inline=True)
    embed.add_field(name="💬 Clan Chat", value="[Stay updated](https://discord.com/channels/1272629330115297330/1272875477555482666)", inline=True)
    embed.add_field(name="🏹 Team Finder", value="[Find PVM teams](https://discord.com/channels/1272629330115297330/1272648555772776529)", inline=True)
    embed.add_field(name="📢 Events", value="[Check upcoming events](https://discord.com/channels/1272629330115297330/1272646577432825977)", inline=True)
    embed.add_field(name="⚔️ Rank Up", value="[Request a rank up](https://discord.com/channels/1272629330115297330/1272648472184487937)\n", inline=True)
    embed.add_field(name=" ", value=" ", inline=True)
    embed.add_field(name="🎓 Mentor Info", value="", inline=True)
    embed.add_field(name=" ", value=" ", inline=True)
    embed.add_field(
        name=(
            "<:corporal:1406217420187893771> **Want to learn raids?**\n"
            "Once you've been here for two weeks and earned your "
            "<:corporal:1406217420187893771> rank, you can open a mentor ticket "
            "for guidance on PVM!"
        ),
        value="", inline=True
    )
    embed.add_field(
        name=(
            "<:mentor:1406802212382052412> **Want to mentor others?**\n"
            "Please open a mentor rank request in <#1272648472184487937>. "
            "State which raid you’d like to mentor and an admin will reach out to you."
        ),
        value="", inline=True
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

    # ---------------------------
    # Update ticket scoreboard
    # ---------------------------
   
    loop = asyncio.get_running_loop()

    def update_score():
        mod_name = interaction.user.display_name
        try:
            cell = ticket_scores_sheet.find(mod_name)
            row = cell.row if cell else None
        except Exception:
            row = None

        if not row:
            ticket_scores_sheet.append_row([mod_name, "0", "0", "0"])
            cell = ticket_scores_sheet.find(mod_name)
            row = cell.row

        values = ticket_scores_sheet.row_values(row)
        while len(values) < 4:
            values.append("0")

        overall = int(values[1]) + 1
        weekly = int(values[2]) + 1
        monthly = int(values[3]) + 1

        ticket_scores_sheet.update(f"B{row}:D{row}", [[overall, weekly, monthly]])

    await loop.run_in_executor(None, update_score)

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
        self.add_item(RoleButton("PvP", "💀"))

# ---------------------------
# 🔹 RSN Commands
# ---------------------------
rsn_write_queue = asyncio.Queue()

async def rsn_writer():
    """Background worker for writing RSNs to Google Sheets."""
    while True:
        member: discord.Member
        rsn_value: str
        member, rsn_value = await rsn_write_queue.get()
        try:
            cell = rsn_sheet.find(str(member.id))
            now = datetime.now(timezone.utc)
            day = now.day  # integer day (no leading zero)
            timestamp = now.strftime(f"%B {day}, %Y at %I:%M%p")

            if cell is not None:
                old_rsn = rsn_sheet.cell(cell.row, 4).value or ""
                rsn_sheet.update_cell(cell.row, 4, rsn_value)
                rsn_sheet.update_cell(cell.row, 5, timestamp)
                print(f"✅ Updated RSN for {member} ({member.id}) to {rsn_value}")
            else:
                old_rsn = ""
                rsn_sheet.append_row([
                    member.display_name,  # current Discord display name
                    str(member.id),
                    old_rsn,
                    rsn_value,
                    timestamp
                ])
                print(f"✅ Added new RSN for {member} ({member.id}) as {rsn_value}")

        except Exception as e:
            print(f"❌ Error writing RSN to sheet for {member}: {e}")
        finally:
            rsn_write_queue.task_done()

class RSNModal(discord.ui.Modal, title="Register RSN"):
    rsn = discord.ui.TextInput(label="RuneScape Name", placeholder="Enter your RSN")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            # enqueue the update instead of writing directly
            await rsn_write_queue.put((interaction.user, str(self.rsn)))

            # Quick acknowledgement
            await interaction.followup.send(
                f"✅ Your RSN **{self.rsn}** has been submitted! "
                "It will be saved in the records shortly.",
                ephemeral=True
            )

            # add role after successful registration
            guild = interaction.guild
            registered_role = discord.utils.get(guild.roles, name="Registered")
            if registered_role and registered_role not in interaction.user.roles:
                await interaction.user.add_roles(registered_role)
                await interaction.followup.send(
                    f"🎉 You’ve been given the {registered_role.mention} role!",
                    ephemeral=True
                )

            # attempt nickname change
            try:
                await interaction.user.edit(nick=str(self.rsn))
            except discord.Forbidden:
                await interaction.followup.send(
                    "⚠️ I don't have permission to change your nickname. "
                    "Please update it manually.",
                    ephemeral=True
                )

        except Exception as e:
            await interaction.followup.send(
                f"❌ Failed to update RSN: `{e}`",
                ephemeral=True
            )


class RSNPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

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

    for row in records:
        name = row.get("Name")
        amount = int(row.get("Amount", 0))
        entry_type = row.get("Type", "").lower()

        if entry_type == "holding":
            inferred_holders[name] = amount
        elif entry_type == "owed":
            inferred_owed[name] = amount

    holders = {k: v for k, v in inferred_holders.items() if v > 0}
    owed = {k: v for k, v in inferred_owed.items() if v > 0}

    return total, holders, owed


def escape_markdown(text: str) -> str:
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

            if current_holding > 0:
                new_holding = max(current_holding - amount, 0)
            else:
                new_holding = 0

            log_coffer_entry(name, new_holding, "holding", 0)

            verb = "deposited"
            formatted_amount = format_million(amount)

            await interaction.response.send_message(
                f"{CUSTOM_EMOJI} {name} {verb} {formatted_amount}!",
                ephemeral=False
            )

        else:
            log_coffer_entry(name, amount, "withdraw", -amount)

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

    _, holders, _ = get_current_total_and_holders_and_owed()
    current_amt = holders.get(name, 0)

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
    await channel.send(":identification_card: **Link your RSN by clicking below to join the server.\nUse /rsn here to check!**", view=RSNPanelView())

async def send_time_panel(channel: discord.TextChannel):
    await channel.purge(limit=10)
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

    def __init__(self, parent_message: discord.Message, requester: discord.User):
        super().__init__()
        self.parent_message = parent_message
        self.requester = requester

    async def on_submit(self, interaction: discord.Interaction):
        entered_name = str(self.target_username.value).strip()
        guild = interaction.guild

        target_member = discord.utils.find(
            lambda m: m.name == entered_name or m.display_name == entered_name,
            guild.members
        )

        if not target_member:
            await interaction.response.send_message(
                "❌ User not found. Please ensure the name matches exactly.",
                ephemeral=True
            )
            return

        await self.parent_message.reply(
            f"{self.requester.mention} is requesting their item from {target_member.mention}",
            mention_author=True,
        )
        await interaction.response.send_message("Request sent ✅", ephemeral=True)


class CollatButtons(discord.ui.View):
    def __init__(self, author: discord.User, mentioned: discord.User | None):
        super().__init__(timeout=None)
        self.author = author
        self.mentioned = mentioned

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
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
            await interaction.response.send_modal(CollatRequestModal(interaction.message, interaction.user))
            return

        target = self.mentioned if interaction.user == self.author else self.author

        await interaction.response.defer()
        await interaction.message.reply(
            f"{interaction.user.mention} is requesting their item from {target.mention}.",
            mention_author=True
        )

    @discord.ui.button(label="Item Returned", style=discord.ButtonStyle.success, emoji="📥")
    async def item_returned(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.disable_all(interaction)
        await interaction.response.send_message("Item marked as returned. ✅", ephemeral=True)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    parent_channel_id = None
    if isinstance(message.channel, discord.Thread):
        parent_channel_id = message.channel.parent.id
    elif isinstance(message.channel, discord.TextChannel):
        parent_channel_id = message.channel.id

    # ---------------------------
    # 🎟️ Ticket message scores
    # ---------------------------
    if parent_channel_id in WATCH_CHANNEL_IDS:
        if any(role.id == STAFF_ROLE_ID for role in message.author.roles):
            display_name = message.author.nick or message.author.name
            print(f"[DEBUG] Incrementing message score for {display_name} in {message.channel.name}")

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, increment_message_score, message.author)

    # ---------------------------
    # 📸 Collat handler
    # ---------------------------
    if message.channel.id == COLLAT_CHANNEL_ID:
        print(f"[DEBUG] Message detected in collat channel {COLLAT_CHANNEL_ID}")
        print(f"[DEBUG] Attachments: {len(message.attachments)} | Mentions: {len(message.mentions)} | Embeds: {len(message.embeds)} | Reply: {message.reference}")
    
        has_pasted_image = any(embed.image for embed in message.embeds)
    
        is_reply = message.reference is not None
        valid_mention = None
        if message.mentions and not is_reply:
            valid_mention = message.mentions[0]
    
        if valid_mention or message.attachments or has_pasted_image:
            print(f"[DEBUG] ✅ Triggering collat buttons | Mention: {valid_mention} | Attachments: {len(message.attachments)} | Pasted: {has_pasted_image}")
            view = CollatButtons(message.author, valid_mention)
            await message.reply("Collat actions:", view=view)
        else:
            print("[DEBUG] ❌ No explicit @mention or screenshot, skipping collat buttons.")

    await bot.process_commands(message)

# ---------------------------
# 🔹 Configuration
# ---------------------------

CHANNEL_ID = 1338295765759688767
CST = ZoneInfo("America/Chicago")

MENTOR_ROLE = 1306021911830073414
SANG_ROLE = 1387153629072592916
TOB_ROLE = 1272694636921753701
EVENTS_ROLE = 1298358942887317555

# ---------------------------
# 🔹 Sanguine Sunday Message
# ---------------------------
SANG_MESSAGE = f"""Sanguine Sunday Sign Up - Hosted by Macflag 
Looking for a fun Sunday activity? Look no farther than Sanguine Sunday! Spend an afternoon/evening sending TOBs with clan members. The focus on this event is on Learners and general KC.

We plan to have mentors on hand to help out with the learners. Learner is someone who need the mechanics explained for each room. 

LEARNERS - please review this thread, watch the xzact guides, and get your plugins setup before Sunday - <#1388887895837773895>

No matter if you're a learner or an experienced raider, we STRONGLY ENCOURAGE you use one of the setups in this thread. We have setups for both learners and experienced (rancour meta setup) - <#1388884558191268070>

If you want to participate, leave a reaction to the post depending on your skill level. 

⚪ - Learner
🔵 - Proficient
🔴 - Mentor

https://discord.com/events/1272629330115297330/1386302870646816788

||<@&{MENTOR_ROLE}> <@&{SANG_ROLE}> <@&{TOB_ROLE}> <@&{EVENTS_ROLE}>||
"""

# ---------------------------
# 🔹 Manual Slash Command
# ---------------------------

@bot.tree.command(name="sangsignup", description="Post the Sanguine Sunday signup message")
@app_commands.describe(channel="Optional channel where the signup should be posted")
async def sangsignup(interaction: discord.Interaction, channel: discord.TextChannel | None = None):
    if not any(r.id == STAFF_ROLE_ID for r in interaction.user.roles):
        await interaction.response.send_message(
            "❌ You don’t have permission to use this command.",
            ephemeral=True
        )
        return

    target_channel = channel or interaction.channel
    if target_channel:
        msg = await target_channel.send(SANG_MESSAGE)
        await msg.add_reaction("⚪")
        await msg.add_reaction("🔵")
        await msg.add_reaction("🔴")
        await interaction.response.send_message(
            f"✅ Sanguine Sunday signup posted in {target_channel.mention}",
            ephemeral=True
        )
    else:
        await interaction.response.send_message("⚠️ Could not resolve a channel.", ephemeral=True)

# ---------------------------
# 🔹 Scheduled Task
# ---------------------------

@tasks.loop(minutes=1)
async def weekly_sangsignup():
    now = datetime.now(CST)
    # Friday 11:00 AM CST
    if now.weekday() == 4 and now.hour == 11 and now.minute == 0:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            msg = await channel.send(SANG_MESSAGE)
            await msg.add_reaction("⚪")
            await msg.add_reaction("🔵")
            await msg.add_reaction("🔴")

@weekly_sangsignup.before_loop
async def before_weekly_sangsignup():
    await bot.wait_until_ready()

# ---------------------------
# 🔹 Bot Events
# ---------------------------

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

    if not reset_scores.is_running():
        reset_scores.start()

    if not weekly_sangsignup.is_running():
        weekly_sangsignup.start()

    rsn_channel = bot.get_channel(1280532494139002912)
    if rsn_channel:
        await send_rsn_panel(rsn_channel)

    time_channel = bot.get_channel(1398775387139342386)
    if time_channel:
        await send_time_panel(time_channel)

    role_channel = bot.get_channel(1272648586198519818)
    if role_channel:
        guild = role_channel.guild

        async for msg in role_channel.history(limit=100):
            if msg.author == bot.user:
                await msg.delete()
        
        await role_channel.send("Select your roles below:")

        raid_embed = discord.Embed(title="⚔︎ ℜ𝔞𝔦𝔡𝔰 ⚔︎", description="", color=0x00ff00)
        await role_channel.send(embed=raid_embed, view=RaidsView(guild))

        boss_embed = discord.Embed(title="⚔︎ 𝔊𝔯𝔬𝔲𝔭 𝔅𝔬𝔰𝔰𝔢𝔰 ⚔︎", description="", color=0x0000ff)
        await role_channel.send(embed=boss_embed, view=BossesView(guild))

        events_embed = discord.Embed(title="⚔︎ 𝔈𝔳𝔢𝔫𝔱𝔰 ⚔︎", description="", color=0xffff00)
        await role_channel.send(embed=events_embed, view=EventsView(guild))
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands.")
    except Exception as e:
        print(f"❌ Command sync failed: {e}")

# ---------------------------
# 🔹 Run Bot
# ---------------------------
bot.run(os.getenv('DISCORD_BOT_TOKEN'))
