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
# 🔹 Info Command
# ---------------------------
@bot.tree.command(name="info", description="Post general information about the clan.")
@app_commands.checks.has_any_role("Moderators")
async def info(interaction: discord.Interaction):
    """Posts a general information embed for the clan."""
    # Defer the response to give the bot more than 3 seconds to process.
    await interaction.response.defer(ephemeral=True, thinking=True)

    # Sending the initial banner image
    await interaction.channel.send("https://i.postimg.cc/8G3CWSDP/info.png")
    await asyncio.sleep(0.5)

    # --- Main Info Embed ---
    info_embed = discord.Embed(
        title="Rancour PvM - Clan Information",
        description="""We are a social, international PvM clan where community, fairness, transparency, and fun are our top priorities.
        We encourage our members to be social; our clan chat is our main hub of communication.
        This is an adult (18+) clan that we want to feel like a home away from home. All we ask is that you show respect to your fellow clanmates.""",
        color=discord.Color.from_rgb(184, 249, 249)
    )
    await interaction.channel.send(embed=info_embed)
    await asyncio.sleep(0.5)

    await interaction.channel.send("https://i.postimg.cc/Zn7d5nwq/border.png")
    await asyncio.sleep(0.5)
    
    # --- What We Offer Embed ---
    offer_embed = discord.Embed(
        title="What We Offer",
        description="""➤ PvM of all levels
        ➤ Skilling and Bossing Competitions
        ➤ Raids - and learner friendly raids
        ➤ Games/Bingos - win huge prizes
        ➤ Social Events - come and hang out!
        ➤ ToB Learner Events - hosted by MacFlag
        ➤ Mentoring - happy to assist""",
        color=discord.Color.from_rgb(197, 236, 236)
    )
    await interaction.channel.send(embed=offer_embed)
    await asyncio.sleep(0.5)

    # --- Requirements Embed ---
    requirements_embed = discord.Embed(
        title="Our Requirements",
        description="""༒ 115+ Combat
        ༒ 1700+ Total Level
        ༒ Medium Combat Achievements
        ༒ Barrows Gloves
        ༒ Dragon Defender
        ༒ Fire Cape
        ༒ Ava’s Assembler
        ༒ MA2 Cape
        ༒ Full Void
        ༒ Any: Torso/Bandos/Torva/Oathplate
        ༒ Piety, Thralls
        ༒ 1/3: BGS/DWH/Elder Maul""",
        color=discord.Color.from_rgb(210, 223, 223)
    )
    await interaction.channel.send(embed=requirements_embed)
    await asyncio.sleep(0.5)

    # --- Systems Embed ---
    systems_embed = discord.Embed(
        title="Clan Ticket Systems and Name Changing",
        description="""👋 **Become a member:** <#1272648453264248852> - Welcome!
        🍌 **Request a rank up:** <#1272648472184487937> - Update your ranks here.
        🔔 **Get help (Support):** <#1272648498554077304> - Report rule-breaking or bot failures, get private help, make suggestions, and more!
        🔑 **Register your RSN:** <#1280532494139002912> - Use this for name changes.

        Guests are always welcome to hang out and get a feel for our community before becoming a member. Just ask!""",
        color=discord.Color.from_rgb(223, 210, 210)
    )
    await interaction.channel.send(embed=systems_embed)
    await asyncio.sleep(0.5)

    # --- Key Channels & Roles Embed ---
    key_channels_embed = discord.Embed(
        title="Key Channels & Roles",
        description="""🎯 **Self-Roles:** Grab your roles in <#1272648586198519818> to get pings for bosses, raids, and events.
        🏹 **Team Finder:** Looking for a group? Head over to <#1272648555772776529>.
        🎉 **Events:** Check out all upcoming clan events in <#1272646577432825977>.
        ✨ **Achievements:** Share your drops and level-ups in <#1272629331524587624>.
        <:mentor:1406802212382052412> **Mentoring:** After two weeks and earning the <:corporal:1406217420187893771> rank, you can open a mentor ticket for PVM guidance. Experienced players can apply to become a mentor in <#1272648472184487937>.""",
        color=discord.Color.from_rgb(236, 197, 197)
    )
    await interaction.channel.send(embed=key_channels_embed)
    await asyncio.sleep(0.5)

    # --- Timezones Embed ---
    timezones_embed = discord.Embed(
        title="Timezones & Active Hours",
        description="""Our clan has members from all over the world! We are most active during the EU and NA evenings.
        You can select your timezone role in 🌐 <#1398775387139342386> to get pings for events in your local time.""",
        color=discord.Color.from_rgb(249, 184, 184)
    )
    await interaction.channel.send(embed=timezones_embed)
    await asyncio.sleep(0.5)
    
    await interaction.channel.send("https://discord.gg/rancour-pvm")
    await interaction.followup.send("✅ Info message has been posted.", ephemeral=True)

# ---------------------------
# 🔹 Rules Command (Refactored)
# ---------------------------
@bot.tree.command(name="rules", description="Post the clan rules message.")
@app_commands.checks.has_any_role("Moderators")
async def rules(interaction: discord.Interaction):
    """Posts a series of embeds detailing the clan rules."""
    await interaction.response.defer(ephemeral=True, thinking=True)

    await interaction.channel.send("https://i.postimg.cc/wgHTWrLJ/rules.png")
    await asyncio.sleep(0.5)

    embed_welcome = discord.Embed(
        description="""`Welcome! Before joining the conversations in the clan, please take a moment to review our rules. They are designed to keep the community fun and respectful for everyone, and are very simple. Please note that Staff and Mods may issue warnings or ban at their discretion if they feel it is necessary to maintain a positive environment.`

        **Discord is a clan requirement**
        We use it for announcements, events, clan discussions, and a wide range of other purposes. We also suggest members **not** mute the <#1272646547020185704> channel.

        *We'll do our best to minimise the pings, but this is for important information you might need if you're going to be a member of the community.*""",
        color=discord.Color.from_rgb(217, 0, 0)
    )
    await interaction.channel.send(embed=embed_welcome)
    await asyncio.sleep(0.5)

    await interaction.channel.send("https://i.postimg.cc/3wcbhGNN/rules-strikes.png")
    await asyncio.sleep(0.5)

    embed_strikes = discord.Embed(
        title="❗The 3-Strike System❗",
        description="""Our community uses a 3-strike system to manage rule violations. The only exception is if someone’s conduct is severe enough to require immediate action.

        ➤ **1st Offence:** Will result in a recorded warning.
        ➤ **2nd Offence:** Second recorded warning and a temporary time-out.
        ➤ **3rd Offence:** Immediate removal from the clan.

        You can appeal a warning or ban by contacting a **Moderator**. Appeals are usually handled via a *voice call*, where you will explain your actions and discuss what is considered acceptable behaviour within the clan.

        Anyone who receives a warning or ban may appeal to have it removed if they feel it was unjust by contacting an admin.""",
        color=discord.Color.from_rgb(211, 1, 1)
    )
    await interaction.channel.send(embed=embed_strikes)
    await asyncio.sleep(0.5)

    await interaction.channel.send("http://i.postimg.cc/TPpCtP06/rules-text.png")
    await asyncio.sleep(0.5)

    rule_data = [
        ("Rule 1️⃣ - Respect Others", "Being respectful to others means treating people the way you’d like to be treated. Another way to look at it is: don’t say anything if you have nothing nice to say, and don’t put others down because they are less experienced than you."),
        ("Rule 2️⃣ - Follow All In-Game & Discord Rules", "This should go without saying, but if rule-breaking is inappropriate for Jagex, it is also inappropriate here.\n\nThe following will **NOT** be tolerated:\n\n⊘ Racism\n⊘ Macroing\n⊘ Solicitation\n⊘ Advertising websites for GP\n⊘ Scamming\n⊘ Ethnic slurs\n⊘ Hate speech"),
        ("Rule 3️⃣ - No Heated Religious or Political Arguments", "Political or religious topics can easily become hectic. Discussing them is fine, as they are part of everyday life, but if a conversation turns into a debate, we kindly ask you to take it to your DMs."),
        ("Rule 4️⃣ - Don’t Share Others' Personal Information", "You are welcome to share your own personal information, but sharing other people’s personal information without consent will result in a warning if it's light enough or a possible ban. Trust is important, and breaking it with people in our community, or with friends, will make you unwelcome in the clan."),
        ("Rule 5️⃣ - No Sharing or Using Plug-ins from Unofficial Clients", "Cheat plug-ins or plug-ins aimed at scamming others through downloads are not allowed, both in-game and on a Discord. These plug-ins are often dangerous and can lead to being banned if undeniable proof is given to us."),
        ("Rule 6️⃣ - No Scamming, Luring, or Begging", "Social engineering, scamming, and luring will result in a RuneWatch case and a ban from the clan, whether it happens to people inside or outside of the clan.\nBegging is extremely irritating and will result in a warning."),
        ("Rule 7️⃣ - All Uniques Must Be Split", "Any unique obtained in group content **must be split** unless stated otherwise before the raid and **agreed upon by all members - This includes members joining your raid**.\nYou also need to split loot with your team members (who are in the clan) **even if** you are doing content on an FFA world, in an FFA clan chat, or if you are an Ironman."),
        ("Rule 8️⃣ - You Must Have Your In-Game Name Set As Your Discord Name", "In order to keep track of clan members during events and reach out to you, you **MUST** have your Discord nickname include your in-game name.\n\n**Acceptable Formats:**\n✅ `- Discord Name / In-Game Name`\n✅ `- Discord Name (In-Game Name)`\n✅ `- In-Game Name Only`\n❌ `- Discord Name Only`\n\n**Enforcement:**\n*We will attempt to replace your name for you, but may reach out if we do not find an in-game match. If you do not reply, you may be mistakenly removed from the Discord.*")
    ]

    rule_colors = [
        (206, 2, 2), (201, 4, 4), (195, 5, 5), (190, 6, 6),
        (185, 7, 7), (179, 9, 9), (174, 10, 10), (168, 12, 12)
    ]

    rule_embeds = [
        discord.Embed(title=title, description=description, color=discord.Color.from_rgb(*rule_colors[i]))
        for i, (title, description) in enumerate(rule_data)
    ]

    await interaction.channel.send(embeds=rule_embeds)
    await interaction.followup.send("✅ Rules message has been posted.", ephemeral=True)

# ---------------------------
# 🔹 Rank Command
# ---------------------------
@bot.tree.command(name="rank", description="Post the clan rank requirements.")
@app_commands.checks.has_any_role("Moderators")
async def rank(interaction: discord.Interaction):
    """Posts a series of embeds detailing the clan rank requirements."""
    await interaction.response.defer(ephemeral=True, thinking=True)

    await interaction.channel.send("https://i.postimg.cc/FmWGMS1G/roles.png")
    await asyncio.sleep(0.5)
    
    # --- Rank Up Instructions Embed ---
    rank_up_embed = discord.Embed(
        title="Rank Up",
        description="""# Please upload screenshots to demonstrate that you meet the requirements for the selected rank.:hourglass: #
## **Important:** :loudspeaker: ##
### 1. No Bank Screenshots! :no_entry_sign: :bank: ###
### 2. Full client screenshots with chatbox open :camera: ###
### 3. Please make sure you meet the requirements :crossed_swords: ###
### 4. Your server nickname should match/contain your RSN :bust_in_silhouette: ###""",
        color=discord.Color.light_grey()
    )

    await interaction.channel.send(embed=rank_up_embed)
    await asyncio.sleep(0.5)

    # --- Recruit Embed ---
    recruit_embed = discord.Embed(
        title="Recruit - <:recruit:1406214952808873994>",
        description="""✦ 115+ Combat, 1700+ Total
✦ Medium Combat Achievements
✦ Barrows Gloves, Dragon Defender
✦ Fire Cape, Ava’s Assembler, MA2 Cape
✦ Full Void
✦ Any: Torso / Bandos / Torva
✦ Piety, Thralls
✦ 1/3: BGS/DWH/Elder Maul""",
        color=discord.Color.from_rgb(255, 215, 0)  # Gold
    )
    await interaction.channel.send(embed=recruit_embed)
    await asyncio.sleep(0.5)

    # --- Corporal Embed ---
    corporal_embed = discord.Embed(
        title="Corporal - <:corporal:1406217420187893771>",
        description="""✦ 2 Weeks in the Clan
✦ Will be automatically applied""",
        color=discord.Color.from_rgb(255, 165, 0)  # Orange
    )
    await interaction.channel.send(embed=corporal_embed)
    await asyncio.sleep(0.5)

    # --- Sergeant Embed ---
    sergeant_embed = discord.Embed(
        title="Sergeant - <:sergeant:1406217456783200417>",
        description="""✦ 4 Weeks in the Clan
✦ 120+ Combat
✦ Hard Combat Achievements
✦ 150+ total raids KC
✦ 85 Farming, 78 Herblore
✦ Elite Void
✦ Crystal Halberd""",
        color=discord.Color.from_rgb(255, 255, 0)  # Yellow
    )
    await interaction.channel.send(embed=sergeant_embed)
    await asyncio.sleep(0.5)

    # --- TzTok Embed ---
    tztok_embed = discord.Embed(
        title="TzTok - <:tztok:1406219778502168647>",
        description="""✦ 6 Weeks in the Clan
✦ 25 minimum KC each: COX / TOB / TOA
✦ 300+ total raids KC
✦ Rigour, Augury, Avernic Defender
✦ 1/3: BOWFA / ZCB / any Mega
✦ 1/3: Fang Kit / Infernal Cape / Quiver
✦ 91 Slayer""",
        color=discord.Color.from_rgb(252, 128, 40)  # Bright Orange
    )
    await interaction.channel.send(embed=tztok_embed)
    await asyncio.sleep(0.5)

    # --- Officer Embed ---
    officer_embed = discord.Embed(
        title="Officer - <:officer:1406225471003299942>",
        description="""✦ 8 Weeks in the Clan
✦ Elite Combat Achievements
✦ 25 minimum KC each: CM / HMT / expTOA
✦ 2/3: Fang Kit / Infernal Cape / Quiver
✦ 1/3: Tbow / Shadow / Scythe
✦ 95 Slayer""",
        color=discord.Color.from_rgb(252, 111, 27)  # Orange-Red
    )
    await interaction.channel.send(embed=officer_embed)
    await asyncio.sleep(0.5)

    # --- Commander Embed ---
    commander_embed = discord.Embed(
        title="Commander - <:commander:1406225531128647782>",
        description="""✦ 12 Weeks in the Clan
✦ 125 Combat
✦ Master Combat Achievements
✦ 50 KC each: CM / HMT / expTOA
✦ 3/3: Fang Kit / Infernal Cape / Quiver
✦ 2/3: Tbow / Shadow / Scythe""",
        color=discord.Color.from_rgb(252, 94, 14)  # Red-Orange
    )
    await interaction.channel.send(embed=commander_embed)
    await asyncio.sleep(0.5)

    # --- TzKal Embed ---
    tzkal_embed = discord.Embed(
        title="TzKal - <:tzkal:1406218822033080400>",
        description="""✦ Fulfills Commander Requirements
✦ Grandmaster Combat Achievements""",
        color=discord.Color.from_rgb(252, 76, 2)  # Red-Orange
    )
    await interaction.channel.send(embed=tzkal_embed)
    await asyncio.sleep(0.5)

    await interaction.followup.send("✅ Rank message has been posted.", ephemeral=True)
    
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
