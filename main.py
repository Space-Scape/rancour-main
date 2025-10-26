import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from oauth2client.service_account import ServiceAccountCredentials
import gspread # <-- Keep this main import
import asyncio
import re
from discord import ui, ButtonStyle # <-- Added ButtonStyle here
from discord.ui import View, Button, Modal, TextInput # This import fixes 'View', 'Button', etc. not defined
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone, time as dt_time # <-- Aliased dt_time
from zoneinfo import ZoneInfo
# --- Corrected gspread exception import ---
import gspread.exceptions

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
# 🔹 Events Sheet Setup
# ---------------------------

EVENTS_SHEET_ID = "1ycltDSLJeKTLAHzVeYZ6JKwIV5A7md8Lh7IetvVljEc"
events_sheet = sheet_client_coffer.open_by_key(EVENTS_SHEET_ID).worksheet("Event Inputs")

# ---------------------------
# 🔹 Sang Sheet Setup
# ---------------------------
SANG_SHEET_ID = "1CCpDAJO7Cq581yF_-rz3vx7L_BTettVaKglSvOmvTOE" # <-- Specific ID for Sang Signups
SANG_SHEET_TAB_NAME = "SangSignups"
try:
    # Use the specific SANG_SHEET_ID and the main sheet_client
    sang_sheet = sheet_client.open_by_key(SANG_SHEET_ID).worksheet(SANG_SHEET_TAB_NAME)
except gspread.exceptions.WorksheetNotFound: # <-- Use fully qualified name
    # This block runs if the *sheet* (tab) doesn't exist.
    sang_sheet = sheet_client.open_by_key(SANG_SHEET_ID).add_worksheet(title=SANG_SHEET_TAB_NAME, rows="100", cols="20")
    # Add Discord_ID as the first column, which is essential for the bot to find users.
    sang_sheet.append_row(["Discord_ID", "Discord_Name", "Roles Known", "KC", "Has_Scythe", "Proficiency", "Learning Freeze", "Timestamp"])
except (PermissionError, gspread.exceptions.APIError) as e: # <-- Use fully qualified name
    # This block runs if the bot doesn't have permission to access the file at all.
    print(f"🔥 CRITICAL ERROR: Bot does not have permission for Sang Sheet (ID: {SANG_SHEET_ID}).")
    print(f"🔥 Please ensure the service account email ({os.getenv('GOOGLE_CLIENT_EMAIL')}) has 'Editor' permissions on this Google Sheet.")
    print(f"🔥 Error details: {e}")
    sang_sheet = None
except Exception as e:
    print(f"Error initializing Sang Sheet: {e}")
    sang_sheet = None


# ---------------------------
# 🔹 Discord Bot Setup
# ---------------------------

intents = discord.Intents.default()
intents.members = True
intents.message_content = True # Needed for on_message
intents.reactions = True # Needed for reaction tasks
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ---------------------------
# 🔹 Main Configuration
# ---------------------------

# --- ADDED GUILD_ID ---
GUILD_ID = 1272629330115297330 # <-- Added for on_ready view registration

# Channel and Role IDs
SUBMISSION_CHANNEL_ID = 1391921214909579336
REVIEW_CHANNEL_ID = 1391921254034047066
LOG_CHANNEL_ID = 1391921275332722749
BANK_CHANNEL_ID = 1276197776849633404
LISTEN_CHANNEL_ID = 1272875477555482666
COLLAT_CHANNEL_ID = 1272648340940525648
EVENT_SCHEDULE_CHANNEL_ID = 1274957572977197138
SANG_CHANNEL_ID = 1338295765759688767
STAFF_ROLE_ID = 1272635396991221824
MEMBER_ROLE_ID = 1272633036814946324 # <-- Added MEMBER_ROLE_ID
MENTOR_ROLE_ID = 1306021911830073414
SANG_ROLE_ID = 1387153629072592916
TOB_ROLE_ID = 1272694636921753701
EVENTS_ROLE_ID = 1298358942887317555

# --- Justice Panel Config ---
JUSTICE_PANEL_CHANNEL_ID = 1422373286368776314 # Channel where the main panel will be.
SENIOR_STAFF_CHANNEL_ID = 1336473990302142484  # Channel for approval notifications.
ADMINISTRATOR_ROLE_ID = 1272961765034164318   # Role that can approve actions.
SENIOR_STAFF_ROLE_ID = 1336473488159936512    # Role that can approve actions.

# --- NEW SUPPORT PANEL CONFIG ---
SUPPORT_PANEL_CHANNEL_ID = 1422397857142542346 # Channel where the support panel will be.
SUPPORT_TICKET_CHANNEL_ID = 1422397857142542346 # Channel where support tickets are created.


# Other constants
REQUIRED_ROLE_NAME = "Event Staff"
CURRENCY_SYMBOL = " 💰"
WATCH_CHANNEL_IDS = [
    1272648453264248852,
    1272648472184487937
]

# Timezone Definition
CST = ZoneInfo("America/Chicago")


# ---------------------------
# 🔹 Info Command
# ---------------------------
@bot.tree.command(name="info", description="Post general information about the clan.")
@app_commands.checks.has_any_role("Administrators")
async def info(interaction: discord.Interaction):
    """Posts a general information embed for the clan."""
    await interaction.response.defer(ephemeral=True, thinking=True)

    await interaction.channel.send("https://i.postimg.cc/8G3CWSDP/info.png")
    await asyncio.sleep(0.5)

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

    systems_embed = discord.Embed(
        title="1️⃣ Clan Ticket Systems and Name Changing",
        description="""<#1272648453264248852> - Welcome!

        <#1272648472184487937> - Update your ranks here.

        <#1272648498554077304> - Report rule-breaking or bot failures, get private help, make suggestions, and more!

        <#1280532494139002912> - Use this for name changes.

        Guests are always welcome to hang out and get a feel for our community before becoming a member. Just ask!""",
        color=discord.Color.from_rgb(217, 216, 216)
    )
    await interaction.channel.send(embed=systems_embed)
    await asyncio.sleep(0.5)

    key_channels_embed = discord.Embed(
        title="2️⃣ Key Channels & Roles",
        description="""<#1272648586198519818> - assign roles to get pings for bosses, raids, and events.

        <#1272648555772776529> - Looking for a group? Find one here.

        <#1272646577432825977> - Check out all upcoming clan events.
        
        <#1426183325093203979> - The clan event schedule. Events of the day are posted here as well!

        <#1272629331524587624> - Share your drops and level-ups.

        <:mentor:1406802212382052412> **Mentoring:** After two weeks and earning the <:corporal:1406217420187893771> rank, you can open a mentor ticket for PVM guidance. Experienced players can apply to become a mentor in <#1272648472184487937>.""",
        color=discord.Color.from_rgb(228, 205, 205)
    )
    await interaction.channel.send(embed=key_channels_embed)
    await asyncio.sleep(0.5)

    more_channels_embed = discord.Embed(
        title="3️⃣ More Channels & Bots",
        description="""<#1272648340940525648> - For item trades. Post a screenshot and @mention a user to bring up `Request Item` & `Item Returned` buttons.
Requesting pings a user, and Returning locks the buttons.

 <#1272875477555482666> - A real-time feed of the in-game clan chat.

 <#1420951302841831587> and <#1424585001235648624> - A drop leaderboard and clan-wide loot tracker (instructions in <#1424585001235648624>)

 <#1400112943475069029> - Discuss bosses, gear, raids, and strategy.

 <#1340349468712767538> - Hunt down the weekly bounty pet for a prize!

 🎧 **Music Bots:** Use `/play` in <#1409931256967204945> to queue music with Euphony or MatchBox while in a voice channel.

 🔊 **TempVoice Bot:** Create a temporary voice channel in <#1272808271392014336>. Manage your channel's settings (name, limit, waiting room, block others, etc.) in the <#1272808273468325930>. Your settings are saved for next time!""",
        color=discord.Color.from_rgb(239, 194, 194)
    )
    await interaction.channel.send(embed=more_channels_embed)
    await asyncio.sleep(0.5)

    # --- Timezones Embed ---
    timezones_embed = discord.Embed(
        title="4️⃣ Timezones & Active Hours",
        description="""Our clan has members from all over the world! We are most active during the EU and NA evenings.

        You can select your timezone role in <#1398775387139342386> to get pings for events in your local time.""",
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
@app_commands.checks.has_any_role("Administrators")
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
        ("Rule 2️⃣ - Follow All In-Game & Discord Rules", "This should go without saying, but if rule-breaking is inappropriate for Jagex and Discord's ToS, it is also inappropriate here. If you are found to be engaging in this sort of behaviour outside of the clan (**especially if you are staff and are representing the clan**) or are frequenting servers that encourage rule-breaking, it will result in your immediate removal from this server following a ban - staff are also held to a higher standard. We're all adults, and we will take action.\n\nThe following will **NOT** be tolerated:\n\n⊘ Macroing and Cheating\n⊘ Solicitation\n⊘ Advertising RWT websites or RWT servers\n⊘ Buying Items and Services using Real World Trading\n⊘ Scamming or engaging in scams\n⊘ Ethnic slurs, Hate speech, and Racism\n\nBreaking any of these may result in an immediate ban at our discretion."),
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
@app_commands.checks.has_any_role("Administrators")
async def rank(interaction: discord.Interaction):
    """Posts a series of embeds detailing the clan rank requirements."""
    await interaction.response.defer(ephemeral=True, thinking=True)

    await interaction.channel.send("https://i.postimg.cc/FmWGMS1G/roles.png")
    await asyncio.sleep(0.5)

    info_embed = discord.Embed(
        title="How to apply for a role",
        description="""**__How to Rank Up__**
Please scroll down and find the rank you wish to apply for. If you meet the requirements, go to the bottom of the page and select the rank from the drop-down menu.

**Staff Ranks**
Golden Key – CEO Account <:CEO:1420745474058752032>
Silver Key – Leaders <:admin:1406221348942123051>
Gold Star – Senior Staff <:seniorstaff:1406217576404488192>
Silver Star – Staff <:staff:1406217522595762246>
Bronze Star – Trial Staff <:trialmod:1420745477279846430>

**Special Ranks**
Mentor - Raid Leaders <:mentor:1406802212382052412>


**Other Ranks**
Guest of the Clan - <:guest:1406225439172722752>
Templar – Contributor <:serverbooster:1406225321778348042>
Colonel – Top Contributor <:colonel:1420745479750422710>
Boss of the Week Winner <:botw:1298362722856997058>
Skill of the Week Winner <:sotw:1298363808707907685>

**Special Events**
For large-scale events, such as bingo or team competitions, winners will be able to choose their own temporary icon!""",
        color=discord.Color.from_rgb(184, 249, 249)
    )
    await interaction.channel.send(embed=info_embed)
    await asyncio.sleep(0.5)

    rank_up_embed = discord.Embed(
        title="# Please upload screenshots to demonstrate that you meet the requirements for the selected rank.:hourglass: #",
        description="""# **Important:** :loudspeaker: ##
### 1. No Bank Screenshots! :no_entry_sign: :bank: ###
### 2. Full client screenshots with chatbox open :camera: ###
### 3. Please make sure you meet the requirements :crossed_swords: ###
### 4. Your server nickname should match/contain your RSN :bust_in_silhouette: ###
### 5. When skipping ranks please also include all requirements for any ranks you are skipping over. ###""",
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
        description="""✦ Fulfills all previous rank requirements
✦ 4 Weeks in the Clan
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
        description="""✦ Fulfills all previous rank requirements
✦ 6 Weeks in the Clan
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
        description="""✦ Fulfills all previous rank requirements
✦ 8 Weeks in the Clan
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
        description="""✦ Fulfills all previous rank requirements
✦ 12 Weeks in the Clan
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
        description="""✦ Fulfills all previous rank requirements
✦ Grandmaster Combat Achievements""",
        color=discord.Color.from_rgb(252, 76, 2)  # Red-Orange
    )
    await interaction.channel.send(embed=tzkal_embed)
    await asyncio.sleep(0.5)

    # --- Pet Hunter Embed ---
    pet_hunter_embed = discord.Embed(
        title="Pet hunter - <:pethunter:1406225392989114378>",
        description="""
✦ 5 Weeks in the Clan
✦ 20+ Pets
        """,
        color=discord.Color.from_rgb(180, 45, 45)
    )
    await interaction.channel.send(embed=pet_hunter_embed)
    await asyncio.sleep(0.5)

    # --- Clogger Embed ---
    clogger_embed = discord.Embed(
        title="Clogger - <:clogger:1406233084311113808>",
        description="""
✦ 5 Weeks in the Clan
✦ 1000+ Collection Log Slots
        """,
        color=discord.Color.from_rgb(160, 40, 40)
    )
    await interaction.channel.send(embed=clogger_embed)
    await asyncio.sleep(0.5)

    # --- Maxed Embed ---
    maxed_embed = discord.Embed(
        title="Maxed - <:maxed:1426589648141946992>",
        description="""
✦ 5 Weeks in the Clan
✦ 2277 total level
        """,
        color=discord.Color.from_rgb(160, 40, 40)
    )
    await interaction.channel.send(embed=maxed_embed)
    await asyncio.sleep(0.5)

    # --- Achiever Embed ---
    achiever_embed = discord.Embed(
        title="Achiever - <:achiever:1426589654966210571>",
        description="""
✦ 5 Weeks in the Clan
✦ 500+ Collection Log slots
✦ 5+ Ornament Kits (shown in log)
✦ Music Cape
✦ Achievement Diary Cape
✦ 1 unique from each raid (CoX, ToB, ToA)
✦ 5 Pets
✦ Minor Scroll Case completed for all clue tiers
        """,
        color=discord.Color.from_rgb(160, 40, 40)
    )
    await interaction.channel.send(embed=achiever_embed)
    await asyncio.sleep(0.5)


    await interaction.followup.send("✅ Rank message has been posted.", ephemeral=True)

# ---------------------------
# 🔹 Say Command
# ---------------------------
@bot.tree.command(name="say", description="Makes the bot say something in the current channel.")
@app_commands.describe(message="The message you want the bot to say.")
@app_commands.checks.has_any_role("Clan Staff", "Administrators", "Senior Staff", "Staff", "Trial Staff")
async def say(interaction: discord.Interaction, message: str):
    """Makes the bot say something."""
    await interaction.channel.send(message)
    await interaction.response.send_message("✅ Message sent!", ephemeral=True, delete_after=5)

# ---------------------------
# 🔹 Help Command
# ---------------------------
@bot.tree.command(name="help", description="Shows a list of all available commands and what they do.")
async def help(interaction: discord.Interaction):
    """Displays a comprehensive help message with all bot commands."""
    await interaction.response.defer(ephemeral=True, thinking=True)

    embed = discord.Embed(
        title="🤖 Rancour Bot Help",
        description="Here is a list of all the commands you can use. Commands marked with 🔒 are for Staff only.",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="👋 General Commands",
        value="""
        `/help` - Displays this help message.
        `/rsn` - Checks your currently registered RuneScape Name.
        `/timehere [member]` - Shows how long a member has been in the server.
        `/submitdrop` - Opens a modal to submit a boss drop for events.
        """,
        inline=False
    )
   
    embed.add_field(
        name="💰 Clan Coffer Commands",
        value="""
        `/bank` - Shows the current coffer total and who is holding or owed money.
        `/deposit` - Opens a modal to deposit money into the clan coffer.
        `/withdraw` - Opens a modal to withdraw money from the clan coffer.
        `/holding [amount] [user]` - Sets or adds to the amount of money a user is holding.
        `/owed [amount] [user]` - Sets the amount of money a user is owed.
        `/clear_owed [user]` - Clears the owed amount for a specific user.
        `/clear_holding [user]` - Clears the holding amount for a specific user.
        """,
        inline=False
    )

    embed.add_field(
        name="🔒 Staff Commands",
        value="""
        `/info` - Posts the detailed clan information embeds in the current channel.
        `/rules` - Posts the clan rules embeds in the current channel.
        `/rank` - Posts the rank requirement embeds in the current channel.
        `/say [message]` - Makes the bot send the specified message in the current channel.
        `/welcome` - (Used in ticket threads) Welcomes a new member and assigns default roles.
        `/rsn_panel` - Posts the interactive RSN registration panel.
        `/time_panel` - Posts the interactive timezone selection panel.
        `/sangsignup [variant] [channel]` - Manually posts the Sanguine Sunday signup or reminder message.
        `/sangmatch [voice_channel]` - Creates ToB teams from signups in a VC.
        `/justice_panel` - Posts the interactive admin panel for moderation.
        `/support_panel` - Posts the staff support specialty role selector.
        """,
        inline=False
    )

    embed.set_footer(text="Use the commands in the appropriate channels. Contact staff for any issues.")

    await interaction.followup.send(embed=embed, ephemeral=True)

# ---------------------------
# 🔹 Time Command (Renamed to timehere)
# ---------------------------
@bot.tree.command(name="timehere", description="Shows how long a member has been in the server.")
@app_commands.describe(member="The member to check.")
async def timehere(interaction: discord.Interaction, member: discord.Member):
    """Shows how long a member has been in the server, provided they have the 'Member' role."""
    
    # Look for the role by ID
    member_role = discord.utils.get(interaction.guild.roles, id=MEMBER_ROLE_ID)
    
    if not member_role:
        await interaction.response.send_message("⚠️ Error: 'Member' role not found on this server.", ephemeral=True)
        return
        
    if member_role not in member.roles:
        await interaction.response.send_message(f"⚠️ {member.display_name} does not have the 'Member' role.", ephemeral=True)
        return

    # Get the join timestamp (timezone-aware)
    join_date = member.joined_at
    if not join_date:
        await interaction.response.send_message("⚠️ Could not retrieve join date for this member.", ephemeral=True)
        return

    # Calculate duration
    now = datetime.now(timezone.utc)
    duration = now - join_date

    # Format duration into years, months, days
    years = duration.days // 365
    remaining_days = duration.days % 365
    months = remaining_days // 30
    days = remaining_days % 30

    duration_parts = []
    if years > 0:
        duration_parts.append(f"{years} year{'s' if years > 1 else ''}")
    if months > 0:
        duration_parts.append(f"{months} month{'s' if months > 1 else ''}")
    if days > 0 or not duration_parts: # Show days if 0, or if it's the only unit
        duration_parts.append(f"{days} day{'s' if days > 1 else ''}")

    duration_str = ", ".join(duration_parts)

    # Format join date for display
    join_date_str = join_date.strftime("%B %d, %Y at %I:%M %p UTC")

    embed = discord.Embed(
        title=f"Membership Time for {member.display_name}",
        color=member.color
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Total Time in Server", value=duration_str, inline=False)
    embed.add_field(name="Join Date", value=join_date_str, inline=False)
    
    await interaction.response.send_message(embed=embed)


# ---------------------------
# 🔹 Welcome
# ---------------------------
class WelcomeView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Approve & Close", style=ButtonStyle.success, custom_id="approve_and_close")
    async def approve_and_close(self, interaction: discord.Interaction, button: Button):
        # Permission Check
        staff_role = discord.utils.get(interaction.guild.roles, id=STAFF_ROLE_ID)
        if staff_role not in interaction.user.roles:
            await interaction.response.send_message("❌ You do not have permission to use this button.", ephemeral=True)
            return
        
        if not isinstance(interaction.channel, discord.Thread):
            await interaction.response.send_message("❌ This button can only be used in a ticket thread.", ephemeral=True)
            return

        await interaction.response.send_message(f"✅ Ticket approved and closed by {interaction.user.mention}.")
        
        # Lock and archive the thread
        await interaction.channel.edit(locked=True, archived=True)

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
            "(https://discord.com/channels/1272629330115297330/1420752491515215872) "
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

    await interaction.response.send_message(embed=embed, view=WelcomeView())

# -----------------------------
# Role Button & Views
# -----------------------------

class RoleButton(Button):
    def __init__(self, role_name: str, emoji=None):
        super().__init__(label=role_name, style=ButtonStyle.secondary, emoji=emoji, custom_id=role_name)

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

        # Send a message to the channel, then send an ephemeral response, then delete the channel message.
        # This makes the "Thinking..." go away and shows the user feedback.
        msg = await interaction.channel.send(feedback)
        await interaction.response.send_message("Role updated!", ephemeral=True, delete_after=1)
        await asyncio.sleep(2)
        await msg.delete()

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
        # Updated "Sanguine Sunday" role name to match the button
        self.add_item(RoleButton("Sanguine Sunday", get_emoji("sanguine_sunday")))
        self.add_item(RoleButton("PvP", "💀"))

class CloseThreadView(View):
    """A view with a single button to close a support thread."""
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Close", style=ButtonStyle.danger, custom_id="close_support_thread")
    async def close_button(self, interaction: discord.Interaction, button: Button):
        staff_role = discord.utils.get(interaction.guild.roles, id=STAFF_ROLE_ID)
        admin_role = discord.utils.get(interaction.guild.roles, id=ADMINISTRATOR_ROLE_ID)
        user_roles = interaction.user.roles

        if not (staff_role in user_roles or admin_role in user_roles):
            await interaction.response.send_message("❌ You don't have permission to close this ticket.", ephemeral=True)
            return

        if isinstance(interaction.channel, discord.Thread):
            try:
                await interaction.response.defer()
                await interaction.channel.edit(archived=True, locked=True)
            except discord.Forbidden:
                await interaction.followup.send("I don't have permission to archive/lock this thread.", ephemeral=True)
        else:
            await interaction.response.send_message("This button can only be used in a thread.", ephemeral=True)

class SupportTicketActionView(View):
    """A view with Approve/Deny buttons for a support role ticket."""
    def __init__(self, target_user: discord.Member, role_name: str):
        super().__init__(timeout=None)
        self.target_user = target_user
        self.role_name = role_name

    async def disable_all(self, interaction: discord.Interaction):
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

    @ui.button(label="Approve", style=ButtonStyle.success)
    async def approve_button(self, interaction: discord.Interaction, button: Button):
        admin_role = discord.utils.get(interaction.guild.roles, id=ADMINISTRATOR_ROLE_ID)
        if not admin_role or admin_role not in interaction.user.roles:
            await interaction.response.send_message("❌ You don't have permission to approve this request.", ephemeral=True)
            return

        role_to_add = discord.utils.get(interaction.guild.roles, name=self.role_name)
        if not role_to_add:
            await interaction.response.send_message(f"❌ Role '{self.role_name}' could not be found.", ephemeral=True)
            await interaction.message.edit(content=f"Error: Role '{self.role_name}' not found.", view=None, embed=None)
            return

        try:
            await self.target_user.add_roles(role_to_add)
            
            embed = discord.Embed(
                title="✅ Request Approved",
                color=discord.Color.green(),
                description=f"The {self.role_name} role has been granted to {self.target_user.mention}.\nThis thread can now be closed."
            )
            embed.set_footer(text=f"Approved by {interaction.user.display_name}")
            
            # Edit the original message, replacing the view with the close button
            await interaction.response.edit_message(embed=embed, view=CloseThreadView())

        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have the necessary permissions to add this role.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An unexpected error occurred: {e}", ephemeral=True)

    @ui.button(label="Deny", style=ButtonStyle.danger)
    async def deny_button(self, interaction: discord.Interaction, button: Button):
        admin_role = discord.utils.get(interaction.guild.roles, id=ADMINISTRATOR_ROLE_ID)
        if not admin_role or admin_role not in interaction.user.roles:
            await interaction.response.send_message("❌ You don't have permission to deny this request.", ephemeral=True)
            return

        embed = discord.Embed(
            title="❌ Request Denied",
            color=discord.Color.red(),
            description="This ticket will be closed shortly."
        )
        embed.set_footer(text=f"Denied by {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed)

        await self.disable_all(interaction)
        await asyncio.sleep(5) 
        if isinstance(interaction.channel, discord.Thread):
            await interaction.channel.edit(archived=True, locked=True)
            
class SupportTicketButton(Button):
    """A custom button that creates a support ticket thread when clicked."""
    def __init__(self, role_name: str, emoji=None):
        super().__init__(label=role_name, style=ButtonStyle.secondary, emoji=emoji, custom_id=f"support_ticket_{role_name.replace(' ', '_')}")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        support_channel = bot.get_channel(SUPPORT_TICKET_CHANNEL_ID)
        if not support_channel:
            await interaction.followup.send("❌ Error: Support ticket channel not found. Please notify an admin.", ephemeral=True)
            return

        user = interaction.user
        role_name_formatted = self.label.replace("/", "-").replace(" ", "-")
        thread_name = f"{role_name_formatted}-Role-Request-{user.display_name}"

        role_descriptions = {
            "Clan Support": "This ticket is for a general clan support role, covering inquiries on recruitment, the coffer, and rank-ups. Staff with this role are the first point of contact for many member questions.",
            "Technical/Bot Support": "This ticket is for the technical support role, focused on reporting issues with the bot, spreadsheets, or other server functions. An Administrator will be looped in for any necessary code or server changes.",
            "Mentor Support": "This ticket is for the mentor support role, which assists with questions related to PvM learning, raid mechanics, and connecting members with mentors."
        }
        
        description = role_descriptions.get(self.label, "A new support role request has been opened.")


        try:
            thread = await support_channel.create_thread(
                name=thread_name,
                type=discord.ChannelType.private_thread
            )

            await thread.add_user(user)

            admin_role_mention = f"<@&{ADMINISTRATOR_ROLE_ID}>"
            
            embed = discord.Embed(
                title=f"New '{self.label}' Role Request",
                description=description,
                color=discord.Color.blue()
            )
            embed.add_field(name="Requested By", value=user.mention, inline=False)
            embed.set_footer(text="Administrators will assist if designated support staff are unavailable.")

            action_view = SupportTicketActionView(target_user=user, role_name=self.label)
            await thread.send(
                content=f"{admin_role_mention}, a new role request has been submitted.",
                embed=embed,
                view=action_view,
                allowed_mentions=discord.AllowedMentions(roles=True, users=True)
            )

            await interaction.followup.send(f"✅ A support ticket has been created for you in {thread.mention}.", ephemeral=True)

        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to create threads in the support channel.", ephemeral=True)
        except Exception as e:
            print(f"Error creating support thread: {e}")
            await interaction.followup.send("❌ An unexpected error occurred while creating the ticket.", ephemeral=True)

class SupportRoleView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(SupportTicketButton("Clan Support", emoji="🔔"))
        self.add_item(SupportTicketButton("Technical/Bot Support", emoji="🔧"))
        self.add_item(SupportTicketButton("Mentor Support", emoji="🎓"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        staff_role = discord.utils.get(interaction.guild.roles, id=STAFF_ROLE_ID)
        if staff_role in interaction.user.roles:
            return True
        else:
            await interaction.response.send_message("❌ This panel is for Clan Staff only.", ephemeral=True)
            return False
# ---------------------------
# 🔹 RSN Commands
# ---------------------------

rsn_write_queue = asyncio.Queue()

async def rsn_writer():
    """Background worker for writing RSNs to Google Sheets."""
    while True:
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

class RSNModal(Modal, title="Register RSN"):
    rsn = TextInput(label="RuneScape Name", placeholder="Enter your RSN")

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


class RSNPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="Register RSN",
        style=ButtonStyle.success,
        emoji="📝",
        custom_id="register_rsn_button"
    )
    async def register_rsn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(RSNModal())


@tree.command(name="rsn_panel", description="Open the RSN registration panel.")
@app_commands.checks.has_any_role("Administrators")
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
        cell = rsn_sheet.find(member_id, in_column=2) # Check User ID column
        rsn_value = rsn_sheet.cell(cell.row, 4).value
        await interaction.response.send_message(
            f"✅ Your registered RSN is **{rsn_value}**.",
            ephemeral=True
        )
    except gspread.CellNotFound: # <-- Use correct exception name
        await interaction.response.send_message(
            "⚠️ You have not registered an RSN yet. Use the RSN panel to register.",
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

class TimeOfDayView(View):
    def __init__(self, guild, timezone_role, tz_abbr):
        super().__init__(timeout=60)
        self.guild = guild
        self.timezone_role = timezone_role
        self.tz_abbr = tz_abbr

        for tod_label, (emoji, _) in TIME_OF_DAY_DATA.items():
            role = discord.utils.get(guild.roles, name=tod_label)
            if role:
                self.add_item(TimeOfDayButton(tod_label, role, emoji, self.timezone_role, self.tz_abbr))

class TimeOfDayButton(Button):
    def __init__(self, label, role, emoji, timezone_role, tz_abbr):
        super().__init__(label=label, style=ButtonStyle.secondary, emoji=emoji)
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

class TimezoneView(View):
    def __init__(self, guild):
        super().__init__(timeout=None)
        self.guild = guild
        for tz_abbr, (tz_str, flag) in TIMEZONE_DATA.items():
            role = discord.utils.get(guild.roles, name=tz_abbr)
            if role:
                self.add_item(TimezoneButton(tz_abbr, role, tz_str, flag, guild))

class TimezoneButton(Button):
    def __init__(self, tz_abbr, role, tz_str, emoji, guild):
        custom_id = f"timezone-btn:{role.id}"
        super().__init__(label=tz_abbr, style=ButtonStyle.primary, custom_id=custom_id, emoji=emoji)
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
@app_commands.checks.has_any_role("Administrators")
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
    await interaction.response.send_message(embed=embed, view=view)

# ---------------------------
# 🔹 Coffer
# ---------------------------
# (Coffer logic is assumed to be correct and unchanged)

# ---------------------------
# 🔹 Panel Init()
# ---------------------------

async def send_rsn_panel(channel: discord.TextChannel):
    """Posts or updates the RSN panel."""
    if not channel: return
    embed = discord.Embed(
        title="<:1gp:1347684047773499482> Register your RuneScape Name",
        description=(
            "Click the button below to register or update your RuneScape name in the clan records.\n\n"
            "This helps event staff verify drops and track your achievements. 🪙"
        ),
        color=discord.Color.green()
    )
    async for message in channel.history(limit=5):
        if message.author == bot.user and message.embeds and message.embeds[0].title == embed.title:
            return # Panel already exists
    await channel.purge(limit=10)
    await channel.send(embed=embed, view=RSNPanelView())


async def send_time_panel(channel: discord.TextChannel):
    """Posts or updates the Timezone panel."""
    if not channel: return
    view = TimezoneView(channel.guild)
    embed = discord.Embed(
        title="🕒 Select Your Usual Timezones",
        description=(
            "Click the button that best matches the **timezones you are most often playing or active**.\n\n"
            "After selecting, you’ll get another prompt to pick the **time of day** you usually play."
        ),
        color=discord.Color.blurple()
    )
    async for message in channel.history(limit=5):
        if message.author == bot.user and message.embeds and message.embeds[0].title == embed.title:
            return # Panel already exists
    await channel.purge(limit=10)
    await channel.send(embed=embed, view=view)

async def send_support_panel(channel: discord.TextChannel):
    """Posts or updates the support specialty role selection panel."""
    if not channel:
        return
        
    embed = discord.Embed(
        title="🛠️ Staff Support Specialties",
        description="""Clan Staff: Select your area of specialty to assist members more effectively. This helps route member tickets to the most knowledgeable staff member.

🔔 **Clan Support:** For general inquiries, questions, ideas/suggestions, and issues with rank-ups or other problems.
        
🔧 **Technical/Bot Support:** For reporting issues with the bot, spreadsheets, or server functions. Admins are looped in for code/server changes.

🎓 **Mentor Support:** For staff members who are also official mentors and can assist with PvM/raid-related questions from Mentors, Mentor Ticket control, and assist with adding new Mentors.""",
        color=discord.Color.teal()
    )
    
    # Check if the panel already exists
    async for message in channel.history(limit=5):
        if message.author == bot.user and message.embeds and message.embeds[0].title == embed.title:
            # It already exists, do nothing.
            return

    # If it doesn't exist, purge and post.
    await channel.purge(limit=10)
    await channel.send(embed=embed, view=SupportRoleView())


# ---------------------------
# 🔹 Collat Notifier
# ---------------------------

class CollatRequestModal(Modal, title="Request Item"):
    target_username = TextInput(
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

class CollatButtons(View):
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

    @ui.button(label="Request Item", style=ButtonStyle.primary, emoji="🔔")
    async def request_item(self, interaction: discord.Interaction, button: Button):
        if not self.mentioned:
            await interaction.response.send_modal(CollatRequestModal(interaction.message, interaction.user))
            return

        target = self.mentioned if interaction.user == self.author else self.author

        await interaction.response.defer()
        await interaction.message.reply(
            f"{interaction.user.mention} is requesting their item from {target.mention}.",
            mention_author=True
        )

    @ui.button(label="Item Returned", style=ButtonStyle.success, emoji="📥")
    async def item_returned(self, interaction: discord.Interaction, button: Button):
        await self.disable_all(interaction)
        await interaction.response.send_message("Item marked as returned. ✅", ephemeral=True)
        
# --------------------------------------------------
# 🔹 Sanguine Sunday Signup System (REFACTORED)
# --------------------------------------------------

SANG_MESSAGE_IDENTIFIER = "Sanguine Sunday Sign Up"
SANG_MESSAGE = f"""\
# {SANG_MESSAGE_IDENTIFIER} – Hosted by Macflag <:sanguine_sunday:1388100187985154130>

Looking for a fun Sunday activity? Look no farther than **Sanguine Sunday!**
Spend an afternoon or evening sending **Theatre of Blood** runs with clan members.
The focus on this event is on **Learners** and general KC.

We plan to have mentors on hand to help out with the learners.
A learner is someone who needs the mechanics explained for each room.

───────────────────────────────
**ToB Learner Resource Hub**

All Theatre of Blood guides, setups, and related resources are organized here:
➤ [**ToB Resource Hub**](https://discord.com/channels/1272629330115297330/1426262876699496598)

───────────────────────────────

LEARNERS – please review this thread, watch the xzact guides, and get your plugins set up before Sunday:
➤ [**Guides & Plugins**](https://discord.com/channels/1272629330115297330/1388887895837773895)

No matter if you're a learner or an experienced raider, we strongly encourage you to use one of the setups in this thread:

⚪ [**Learner Setups**](https://discord.com/channels/1272629330115297330/1426263868950450257)
🔵 [**Rancour Meta Setups**](https://discord.com/channels/1272629330115297330/1426272592452391012)

───────────────────────────────
**Sign-Up Here!**

Click a button below to sign up for the event.
- **Raider:** Fill out the form with your KC and gear.
- **Mentor:** Fill out the form to sign up as a mentor.

Event link: <https://discord.com/events/1272629330115297330/1386302870646816788>

||<@&{MENTOR_ROLE_ID}> <@&{SANG_ROLE_ID}> <@&{TOB_ROLE_ID}>||
"""

LEARNER_REMINDER_IDENTIFIER = "Sanguine Sunday Learner Reminder"
LEARNER_REMINDER_MESSAGE = f"""\
# {LEARNER_REMINDER_IDENTIFIER} ⏰ <:sanguine_sunday:1388100187985154130>

This is a reminder for all learners who signed up for Sanguine Sunday!

Please make sure you have reviewed the following guides and have your gear and plugins ready to go:
• **[ToB Resource Hub](https://discord.com/channels/1272629330115297330/1426262876699496598)**
• **[Learner Setups](https://discord.com/channels/1272629330115297330/1426263868950450257)**
• **[Rancour Meta Setups](https://discord.com/channels/1272629330115297330/1426272592452391012)**
• **[Guides & Plugins](https://discord.com/channels/1272629330115297330/1426263621440372768)**

We look forward to seeing you there!
"""

class UserSignupForm(Modal, title="Sanguine Sunday Signup"):
    roles_known = TextInput(
        label="Roles known? (Leave blank if None)", # <-- Shortened Label
        placeholder="e.g., All, Nfrz, Sfrz, Mdps, Rdps",
        style=discord.TextStyle.short,
        max_length=100,
        required=False
    )
    
    kc = TextInput(
        label="What is your Normal Mode ToB KC?",
        placeholder="Enter your kill count (e.g., 0, 25, 150)",
        style=discord.TextStyle.short,
        max_length=10,
        required=True
    )

    has_scythe = TextInput(
        label="Do you have a Scythe? (Yes/No)",
        placeholder="Yes or No",
        style=discord.TextStyle.short,
        max_length=5,
        required=True
    )
    
    learning_freeze = TextInput(
        label="Learn freeze role? (Yes/No, blank for No)",
        placeholder="Yes or No",
        style=discord.TextStyle.short,
        max_length=5,
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        if not sang_sheet:
            await interaction.response.send_message("⚠️ Error: The Sanguine Sunday signup sheet is not connected. Please contact staff.", ephemeral=True)
            return

        try:
            kc_value = int(str(self.kc))
            if kc_value < 0:
                raise ValueError("KC cannot be negative.")
        except ValueError:
            await interaction.response.send_message("⚠️ Error: Kill Count must be a valid number.", ephemeral=True)
            return
            
        scythe_value = str(self.has_scythe).strip().lower()
        if scythe_value not in ["yes", "no", "y", "n"]:
            await interaction.response.send_message("⚠️ Error: Scythe must be 'Yes' or 'No'.", ephemeral=True)
            return
        has_scythe_bool = scythe_value in ["yes", "y"]

        proficiency_value = ""
        if kc_value <= 1:
            proficiency_value = "New"
        elif 1 < kc_value < 50:
            proficiency_value = "Learner"
        else:
            proficiency_value = "Proficient"

        roles_known_value = str(self.roles_known).strip() or "None"
        learning_freeze_value = str(self.learning_freeze).strip().lower()
        learning_freeze_bool = learning_freeze_value in ["yes", "y"]

        user_id = str(interaction.user.id)
        user_name = interaction.user.display_name
        timestamp = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S")
        
        row_data = [
            user_id, user_name, roles_known_value, kc_value, 
            has_scythe_bool, proficiency_value, learning_freeze_bool, timestamp
        ]
        
        try:
            # Try to find the user ID in the first column
            cell = sang_sheet.find(user_id, in_column=1)

            # --- UPDATED CHECK ---
            if cell is None:
                # User not found, append a new row
                sang_sheet.append_row(row_data)
            else:
                # User found, update the existing row
                sang_sheet.update(f'A{cell.row}:H{cell.row}', [row_data])
        # Keep the original exception handler just in case find *can* raise it, and correct the name
        except gspread.CellNotFound:
             sang_sheet.append_row(row_data)
        except Exception as e:
            # Handle other potential errors during sheet interaction
            print(f"🔥 GSpread error on signup: {e}")
            await interaction.response.send_message("⚠️ An error occurred while saving your signup.", ephemeral=True)
            return

        # --- Success message (was previously placeholder) ---
        await interaction.response.send_message(
            f"✅ **You are signed up as {proficiency_value}!**\n"
            f"**KC:** {kc_value}\n"
            f"**Scythe:** {'Yes' if has_scythe_bool else 'No'}\n"
            f"**Roles Known:** {roles_known_value}\n"
            f"**Learn Freeze:** {'Yes' if learning_freeze_bool else 'No'}",
            ephemeral=True
        )

class MentorSignupForm(Modal, title="Sanguine Sunday Mentor Signup"):
    roles_known = TextInput(
        label="What roles do you know?",
        placeholder="e.g., All, Nfrz, Sfrz",
        style=discord.TextStyle.short,
        max_length=100,
        required=True
    )
    
    kc = TextInput(
        label="What is your Normal Mode ToB KC?",
        placeholder="Enter your kill count (e.g., 250)",
        style=discord.TextStyle.short,
        max_length=10,
        required=True
    )

    has_scythe = TextInput(
        label="Do you have a Scythe? (Yes/No)",
        placeholder="Yes or No",
        style=discord.TextStyle.short,
        max_length=5,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        if not sang_sheet:
            await interaction.response.send_message("⚠️ Error: The Sanguine Sunday signup sheet is not connected.", ephemeral=True)
            return

        try:
            kc_value = int(str(self.kc))
            if kc_value < 50:
                await interaction.response.send_message("⚠️ Mentors should have 50+ KC to sign up.", ephemeral=True)
                return
        except ValueError:
            await interaction.response.send_message("⚠️ Error: Kill Count must be a valid number.", ephemeral=True)
            return
            
        scythe_value = str(self.has_scythe).strip().lower()
        if scythe_value not in ["yes", "no", "y", "n"]:
            await interaction.response.send_message("⚠️ Error: Scythe must be 'Yes' or 'No'.", ephemeral=True)
            return
        has_scythe_bool = scythe_value in ["yes", "y"]

        proficiency_value = "Mentor"
        roles_known_value = str(self.roles_known).strip()
        learning_freeze_bool = False

        user_id = str(interaction.user.id)
        user_name = interaction.user.display_name
        timestamp = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S")
        
        row_data = [
            user_id, user_name, roles_known_value, kc_value, 
            has_scythe_bool, proficiency_value, learning_freeze_bool, timestamp
        ]
        
        try:
            # Try to find the user ID in the first column
            cell = sang_sheet.find(user_id, in_column=1)

            # --- UPDATED CHECK ---
            if cell is None:
                 # User not found, append a new row
                 sang_sheet.append_row(row_data)
            else:
                 # User found, update the existing row
                 sang_sheet.update(f'A{cell.row}:H{cell.row}', [row_data])
        # Keep the original exception handler and correct the name
        except gspread.CellNotFound:
            sang_sheet.append_row(row_data)
        except Exception as e:
            # Handle other potential errors during sheet interaction
            print(f"🔥 GSpread error on mentor signup: {e}")
            await interaction.response.send_message("⚠️ An error occurred while saving your signup.", ephemeral=True)
            return

        # --- Success message (was previously placeholder) ---
        await interaction.response.send_message(
            f"✅ **You are signed up as a Mentor!**\n"
            f"**KC:** {kc_value}\n"
            f"**Scythe:** {'Yes' if has_scythe_bool else 'No'}\n"
            f"**Roles Known:** {roles_known_value}",
            ephemeral=True
        )

# --- Persistent View for Signup Buttons ---
class SignupView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Sign Up as Raider", style=ButtonStyle.success, custom_id="sang_signup_raider", emoji="📝")
    async def user_signup_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(UserSignupForm())
        
    @ui.button(label="Sign Up as Mentor", style=ButtonStyle.primary, custom_id="sang_signup_mentor", emoji="🎓")
    async def mentor_signup_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(MentorSignupForm())

# --- Helper Functions ---
async def find_latest_signup_message(channel: discord.TextChannel) -> Optional[discord.Message]:
    """Finds the most recent Sanguine Sunday signup message in a channel."""
    async for message in channel.history(limit=100):
        if message.author == bot.user and SANG_MESSAGE_IDENTIFIER in message.content:
            return message
    return None

# --- Core Functions ---
async def post_signup(channel: discord.TextChannel):
    """Posts the main signup message with the signup buttons."""
    await channel.send(SANG_MESSAGE, view=SignupView())
    print(f"✅ Posted Sanguine Sunday signup in #{channel.name}")

async def post_reminder(channel: discord.TextChannel):
    """Finds learners (New or Learner proficiency) from GSheet and posts a reminder."""
    if not sang_sheet:
        print("⚠️ Cannot post reminder, Sang Sheet not connected.")
        return False # Indicate failure

    # Delete previous reminders from the bot
    try:
        async for message in channel.history(limit=50):
            if message.author == bot.user and LEARNER_REMINDER_IDENTIFIER in message.content:
                await message.delete()
    except discord.Forbidden:
        print(f"⚠️ Could not delete old reminders in #{channel.name} (Missing Permissions)")
    except Exception as e:
        print(f"🔥 Error cleaning up reminders: {e}")

    learners = []
    try:
        all_signups = sang_sheet.get_all_records() # Fetch all signups
        for signup in all_signups:
            # Check the Proficiency column (case-insensitive)
            proficiency = str(signup.get("Proficiency", "")).lower()
            if proficiency in ["learner", "new"]:
                user_id = signup.get('Discord_ID')
                if user_id:
                    learners.append(f"<@{user_id}>")

        if not learners:
            reminder_content = f"{LEARNER_REMINDER_MESSAGE}\n\n_No learners have signed up yet._"
        else:
            learner_pings = " ".join(learners)
            reminder_content = f"{LEARNER_REMINDER_MESSAGE}\n\n**Learners:** {learner_pings}"

        await channel.send(reminder_content, allowed_mentions=discord.AllowedMentions(users=True))
        print(f"✅ Posted Sanguine Sunday learner reminder in #{channel.name}")
        return True # Indicate success
    except Exception as e:
        print(f"🔥 GSpread error fetching/posting reminder: {e}")
        await channel.send("⚠️ Error processing learner list from database.")
        return False # Indicate failure

# --- Slash Command Group ---
@bot.tree.command(name="sangsignup", description="Manage Sanguine Sunday signups.")
@app_commands.checks.has_role(STAFF_ROLE_ID)
@app_commands.describe(
    variant="Choose the action to perform.",
    channel="Optional channel to post in (defaults to the configured event channel)."
)
@app_commands.choices(variant=[
    app_commands.Choice(name="Post Signup Message", value=1),
    app_commands.Choice(name="Post Learner Reminder", value=2),
])
async def sangsignup(interaction: discord.Interaction, variant: int, channel: Optional[discord.TextChannel] = None):
    target_channel = channel or bot.get_channel(SANG_CHANNEL_ID)
    if not target_channel:
        await interaction.response.send_message("⚠️ Could not find the target channel.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    if variant == 1:
        await post_signup(target_channel)
        await interaction.followup.send(f"✅ Signup message posted in {target_channel.mention}.")
    elif variant == 2:
        result = await post_reminder(target_channel)
        if result:
            await interaction.followup.send(f"✅ Learner reminder posted in {target_channel.mention}.")
        else:
            await interaction.followup.send("⚠️ Could not post the reminder.")

@sangsignup.error
async def sangsignup_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message("❌ You don't have permission.", ephemeral=True)
    else:
        print(f"Error in sangsignup command: {error}")
        # Use followup if response already sent (due to defer)
        if interaction.response.is_done():
             await interaction.followup.send(f"An unexpected error occurred.", ephemeral=True)
        else:
             await interaction.response.send_message(f"An unexpected error occurred.", ephemeral=True)


# --- Helper function for role parsing ---
def parse_roles(roles_str: str) -> (bool, bool):
    """Parses a roles string to check for range and melee keywords."""
    if not roles_str or roles_str == "N/A":
        return False, False

    roles_str = roles_str.lower()
    knows_range = any(s in roles_str for s in ["range", "ranger", "rdps"])
    knows_melee = any(s in roles_str for s in ["melee", "mdps", "meleer"])
    return knows_range, knows_melee

# --- Helper function to get complementary learners ---
def pop_complementary_learners(learners_list: list) -> (dict, dict):
    """
    Pops the first learner and tries to find a complementary
    (range/melee) learner to pop and return as a pair.
    """
    if not learners_list or len(learners_list) < 2:
        return None, None

    l1 = learners_list.pop(0)
    l1_range, l1_melee = l1.get('knows_range', False), l1.get('knows_melee', False)

    # If l1 doesn't know a specific role, no complement is needed
    if not (l1_range or l1_melee):
        return l1, learners_list.pop(0)

    # Try to find a complement
    for i, l2 in enumerate(learners_list):
        l2_range, l2_melee = l2.get('knows_range', False), l2.get('knows_melee', False)
        # Check for complementary roles
        if (l1_range and l2_melee) or (l1_melee and l2_range):
            return l1, learners_list.pop(i)

    # No complement found, just return the next in line
    return l1, learners_list.pop(0)


# --- Matchmaking Slash Command (REWORKED + Highly Proficient) ---
@bot.tree.command(name="sangmatch", description="Create ToB teams from signups in a voice channel.")
@app_commands.checks.has_role(STAFF_ROLE_ID)
@app_commands.describe(voice_channel="The voice channel to pull active users from.")
async def sangmatch(interaction: discord.Interaction, voice_channel: discord.VoiceChannel):
    if not sang_sheet:
        await interaction.response.send_message("⚠️ Error: The Sanguine Sunday sheet is not connected.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=False) # Send to channel

    # --- 1. Get users in the specified voice channel ---
    if not voice_channel.members:
        await interaction.followup.send(f"⚠️ No users are in {voice_channel.mention}.")
        return

    vc_member_ids = {str(member.id) for member in voice_channel.members if not member.bot}
    if not vc_member_ids:
        await interaction.followup.send(f"⚠️ No human users are in {voice_channel.mention}.")
        return

    # --- 2. Get all signups from GSheet ---
    try:
        all_signups_records = sang_sheet.get_all_records()
        if not all_signups_records:
            await interaction.followup.send("⚠️ There are no signups in the database.")
            return
    except Exception as e:
        print(f"🔥 GSheet error fetching all signups: {e}")
        await interaction.followup.send("⚠️ An error occurred fetching signups from the database.")
        return

    # --- 3. Filter signups to only users in the VC and parse roles ---
    available_raiders = []
    for signup in all_signups_records:
        user_id = str(signup.get("Discord_ID"))
        if user_id in vc_member_ids:
            roles_str = signup.get("Roles Known", "")
            knows_range, knows_melee = parse_roles(roles_str)
            kc_raw = signup.get("KC", 0) # Get KC value, default to 0
            try:
                # Convert KC to int, handle potential non-numeric values (like 'N/A' for mentors)
                kc_val = int(kc_raw)
            except (ValueError, TypeError):
                kc_val = 0 # Default non-numeric KC to 0 for sorting/logic

            # --- Determine Proficiency including Highly Proficient ---
            proficiency_val = ""
            if signup.get("Proficiency", "").lower() == 'mentor':
                proficiency_val = 'mentor'
            elif kc_val <= 1:
                proficiency_val = "new"
            elif 1 < kc_val < 50:
                proficiency_val = "learner"
            elif 50 <= kc_val < 150:
                proficiency_val = "proficient"
            else: # 150+ KC
                proficiency_val = "highly proficient"

            available_raiders.append({
                "user_id": user_id,
                "user_name": signup.get("Discord_Name"),
                "proficiency": proficiency_val, # Use calculated proficiency
                "kc": kc_val, # Use the integer KC value
                "has_scythe": str(signup.get("Has_Scythe", "FALSE")).upper() == "TRUE",
                "roles_known": roles_str,
                "learning_freeze": str(signup.get("Learning Freeze", "FALSE")).upper() == "TRUE",
                "knows_range": knows_range,
                "knows_melee": knows_melee
            })

    if not available_raiders:
        await interaction.followup.send(f"⚠️ None of the users in {voice_channel.mention} have signed up for the event.")
        return

    # --- 4. Matchmaking Logic ---
    teams = []
    used_ids = set()

    # --- 4a. Create player pools ---
    mentors_scythe = [r for r in available_raiders if r['proficiency'] == 'mentor' and r['has_scythe']]
    mentors_no_scythe = [r for r in available_raiders if r['proficiency'] == 'mentor' and not r['has_scythe']]
    highly_proficient_scythe = [r for r in available_raiders if r['proficiency'] == 'highly proficient' and r['has_scythe']]
    highly_proficient_no_scythe = [r for r in available_raiders if r['proficiency'] == 'highly proficient' and not r['has_scythe']]
    proficient_scythe = [r for r in available_raiders if r['proficiency'] == 'proficient' and r['has_scythe']]
    proficient_no_scythe = [r for r in available_raiders if r['proficiency'] == 'proficient' and not r['has_scythe']]

    # Combine HP and P pools for easier selection later, but keep HP prioritized by sorting
    all_proficient_scythe = sorted(highly_proficient_scythe + proficient_scythe, key=lambda x: x['proficiency']=='highly proficient', reverse=True)
    all_proficient_no_scythe = sorted(highly_proficient_no_scythe + proficient_no_scythe, key=lambda x: x['proficiency']=='highly proficient', reverse=True)

    # Sort learners to prioritize range/melee and non-freeze
    learners = sorted([r for r in available_raiders if r['proficiency'] in ['learner', 'new']],
                      key=lambda x: (
                          x['learning_freeze'], # False (non-freeze) comes first
                          not (x['knows_range'] or x['knows_melee']), # False (knows a role) comes first
                          x.get('kc', 0) # Then sort by KC
                      ))

    learners_freeze = [l for l in learners if l['learning_freeze']]
    learners_normal = [l for l in learners if not l['learning_freeze']]

    # --- 4b. Pass 1: Build Ideal (1M, 1L, 2HP/P) Teams ---
    # Loop while we have the components for this ideal team
    while (mentors_scythe or mentors_no_scythe) and (learners_normal or learners_freeze) and (len(all_proficient_scythe) + len(all_proficient_no_scythe) >= 2):
        team = []

        learner = learners_normal.pop(0) if learners_normal else learners_freeze.pop(0)
        team.append(learner)

        # 2. Add Mentor and Proficient players based on Scythe priority
        # Goal: 2+ Scythes or 0 Scythes. Avoid 1 Scythe. Prioritize Highly Proficient.

        # Try for 2+ Scythes (M-S + P-S + P-S/P-NS, prioritize HP)
        if mentors_scythe and all_proficient_scythe:
            team.append(mentors_scythe.pop(0))
            team.append(all_proficient_scythe.pop(0)) # Add best available proficient w/ scythe
            if all_proficient_scythe: team.append(all_proficient_scythe.pop(0)) # 3 scythes (prioritizes HP)
            elif all_proficient_no_scythe: team.append(all_proficient_no_scythe.pop(0)) # 2 scythes (prioritizes HP)
            else:
                # Not enough proficient, put players back
                mentors_scythe.insert(0, team.pop()) # Put mentor back
                all_proficient_scythe.insert(0, team.pop()) # Put first proficient back
                # Put learner back into appropriate list
                if learner['learning_freeze']: learners_freeze.insert(0, team.pop())
                else: learners_normal.insert(0, team.pop())
                continue # Try next pass or exit loop

        # Try for 0 Scythes (M-NS + P-NS + P-NS, prioritize HP)
        elif mentors_no_scythe and len(all_proficient_no_scythe) >= 2:
            team.append(mentors_no_scythe.pop(0))
            team.append(all_proficient_no_scythe.pop(0)) # Add best non-scythe
            team.append(all_proficient_no_scythe.pop(0)) # Add second best non-scythe

        # Try for 1 Scythe (Last resort, prioritize HP)
        # (M-S + P-NS + P-NS)
        elif mentors_scythe and len(all_proficient_no_scythe) >= 2:
            team.append(mentors_scythe.pop(0))
            team.append(all_proficient_no_scythe.pop(0))
            team.append(all_proficient_no_scythe.pop(0))
        # (M-NS + P-S + P-NS)
        elif mentors_no_scythe and all_proficient_scythe and all_proficient_no_scythe:
            team.append(mentors_no_scythe.pop(0))
            team.append(all_proficient_scythe.pop(0))
            team.append(all_proficient_no_scythe.pop(0))
        else:
            # Can't form a 4-man team with the remaining players
            if learner['learning_freeze']: learners_freeze.insert(0, team.pop()) # Put learner back
            else: learners_normal.insert(0, team.pop())
            break # Exit Pass 1

        teams.append(team)
        for member in team:
            used_ids.add(member['user_id'])

    # --- 4c. Pass 2: Fallback (2M, 2L) Teams ---
    # Re-sort remaining learners
    remaining_learners = sorted(learners_normal + learners_freeze,
                                key=lambda x: (not (x['knows_range'] or x['knows_melee']), x['learning_freeze'])) # Prioritize role known, then non-freeze

    while (len(mentors_scythe) + len(mentors_no_scythe) >= 2) and len(remaining_learners) >= 2:
        team = []

        l1, l2 = pop_complementary_learners(remaining_learners)
        if not l1 or not l2: break # Not enough learners
        team.extend([l1, l2])

        # Add 2 Mentors (Prioritize 2+ or 0 Scythes)
        if len(mentors_scythe) >= 2: team.extend([mentors_scythe.pop(0), mentors_scythe.pop(0)])
        elif len(mentors_no_scythe) >= 2: team.extend([mentors_no_scythe.pop(0), mentors_no_scythe.pop(0)])
        elif mentors_scythe and mentors_no_scythe:
            team.append(mentors_scythe.pop(0))
            team.append(mentors_no_scythe.pop(0))
        else:
            # Can't form 2M team
            remaining_learners.insert(0, team.pop()) # Put learners back
            remaining_learners.insert(0, team.pop())
            break # Exit Pass 2

        teams.append(team)
        for member in team: used_ids.add(member['user_id'])

    # --- 4d. Pass 3: Cleanup Leftovers ---
    # Gather all remaining players, including Highly Proficient
    all_remaining_proficient = all_proficient_scythe + all_proficient_no_scythe
    all_pools = mentors_scythe + mentors_no_scythe + all_remaining_proficient + remaining_learners
    leftovers = sorted([r for r in all_pools if r['user_id'] not in used_ids],
                       key=lambda x: (
                           x['proficiency'] == 'highly proficient', # Highest priority
                           x['proficiency'] == 'proficient',
                           x['proficiency'] == 'mentor',
                           x.get('has_scythe', False)
                       ), reverse=True) # Sort best players first

    while len(leftovers) >= 3:
        team_size = 4 # Default to 4
        if len(leftovers) == 4: team_size = 4
        elif len(leftovers) == 5:
            # Check if making a 5-man team includes a 'New' player
            has_new_player = any(p['proficiency'] == 'new' for p in leftovers[:5])
            team_size = 4 if has_new_player else 5 # Make 4-man if 'New' player present
        elif len(leftovers) == 6: team_size = 3 # Make two teams of 3
        elif len(leftovers) > 5: team_size = 4 # Make a 4-man team first
        else: team_size = 3 # Only 3 left

        new_team = leftovers[:team_size]
        teams.append(new_team)
        for member in new_team: used_ids.add(member['user_id'])
        leftovers = leftovers[team_size:]

    # Add final 1 or 2 players if they exist
    if leftovers:
        teams.append(leftovers)
        for member in leftovers: used_ids.add(member['user_id'])

    # --- 5. Format and send output ---
    embed = discord.Embed(
        title=f"Sanguine Sunday Teams - {voice_channel.name}",
        description=f"Created {len(teams)} team(s) from {len(available_raiders)} signed-up users in the VC.",
        color=discord.Color.red()
    )

    if not teams:
        embed.description = "Could not form any teams with the available players."

    for i, team in enumerate(teams):
        team_details = []
        for member in team:
            scythe_text = " (Scythe)" if member.get('has_scythe', False) else ""
            # Display "Highly Proficient" correctly
            role_text = member.get('proficiency', 'Unknown').replace(" ", "-").capitalize().replace("-"," ")
            kc_raw = member.get('kc', 0)
            # Only show KC if it's a number AND (not a Mentor OR Mentor KC > 0)
            kc_text = f"({kc_raw} KC)" if str(kc_raw).isdigit() and (role_text != "Mentor" or kc_raw > 0) else ""

            team_details.append(
                f"<@{member['user_id']}> - **{role_text}** {kc_text}{scythe_text}"
            )
        embed.add_field(name=f"Team {i+1}", value="\n".join(team_details), inline=False)

    unassigned_users = vc_member_ids - used_ids
    if unassigned_users:
        mentions = " ".join([f"<@{uid}>" for uid in unassigned_users])
        embed.add_field(
            name="Unassigned Users in VC",
            value=f"These users were in the VC but were not assigned (either not signed up or left over):\n{mentions}",
            inline=False
        )

    await interaction.followup.send(embed=embed)


@sangmatch.error
async def sangmatch_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message("❌ You don't have permission.", ephemeral=True)
    else:
        print(f"Error in sangmatch command: {error}")
        if not interaction.response.is_done():
            await interaction.response.send_message(f"An unexpected error occurred.", ephemeral=True)
        else:
            await interaction.followup.send(f"An unexpected error occurred.", ephemeral=True)


# --- Scheduled Tasks ---
@tasks.loop(time=dt_time(hour=11, minute=0, tzinfo=CST))
async def scheduled_post_signup():
    """Posts the signup message every Friday at 11:00 AM CST."""
    if datetime.now(CST).weekday() == 4:  # 4 = Friday
        channel = bot.get_channel(SANG_CHANNEL_ID)
        if channel:
            await post_signup(channel)

@tasks.loop(time=dt_time(hour=14, minute=0, tzinfo=CST))
async def scheduled_post_reminder():
    """Posts the learner reminder every Saturday at 2:00 PM CST."""
    if datetime.now(CST).weekday() == 5:  # 5 = Saturday
        channel = bot.get_channel(SANG_CHANNEL_ID)
        if channel:
            await post_reminder(channel)

@scheduled_post_signup.before_loop
@scheduled_post_reminder.before_loop
async def before_scheduled_tasks():
    await bot.wait_until_ready()

# ---------------------------
# 🔹 Justice Panel
# ---------------------------
# (Justice Panel logic is assumed to be correct and unchanged)

# ---------------------------
# 🔹 Bot Events
# ---------------------------

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # This ensures that bot.commands (if any) are still processed
    # await bot.process_commands(message) # Only needed if using prefix commands

    if message.channel.id == COLLAT_CHANNEL_ID:
        has_pasted_image = any(embed.image for embed in message.embeds)
        is_reply = message.reference is not None
        valid_mention = message.mentions[0] if message.mentions and not is_reply else None

        if valid_mention or message.attachments or has_pasted_image:
            view = CollatButtons(message.author, valid_mention)
            await message.reply("Collat actions:", view=view, allowed_mentions=discord.AllowedMentions.none())

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

    # Add persistent views
    # bot.add_view(JusticePanelView())  <-- This class is not defined in the provided file
    bot.add_view(SupportRoleView())
    bot.add_view(RSNPanelView())
    bot.add_view(CloseThreadView())
    bot.add_view(SignupView()) # <-- Added for Sanguine Sunday
    bot.add_view(WelcomeView()) # <-- Added for /welcome command

    # Start the RSN writer task
    asyncio.create_task(rsn_writer())

    # Start the Sanguine Sunday tasks
    if not scheduled_post_signup.is_running():
        scheduled_post_signup.start()
        print("✅ Started scheduled signup task.")
    if not scheduled_post_reminder.is_running():
        scheduled_post_reminder.start()
        print("✅ Started scheduled reminder task.")
    # Removed maintain_reactions task as it's no longer used

    # Panel initializations
    rsn_channel_id = 1280532494139002912
    rsn_channel = bot.get_channel(rsn_channel_id)
    if rsn_channel:
        print("🔄 Checking and posting RSN panel...")
        await send_rsn_panel(rsn_channel)
        print("✅ RSN panel posted.")

    time_channel_id = 1398775387139342386
    time_channel = bot.get_channel(time_channel_id)
    if time_channel:
        print("🔄 Checking and posting Timezone panel...")
        guild = time_channel.guild # Get guild from channel
        bot.add_view(TimezoneView(guild)) # Register view
        await send_time_panel(time_channel)
        print("✅ Timezone panel posted.")

    support_channel_id = SUPPORT_PANEL_CHANNEL_ID
    support_channel = bot.get_channel(support_channel_id)
    if support_channel:
        print("🔄 Checking and posting Support panel...")
        await send_support_panel(support_channel)
        print(f"✅ Posted support panel in #{support_channel.name}.")

    role_channel_id = 1272648586198519818
    role_channel = bot.get_channel(role_channel_id)
    if role_channel:
        guild = role_channel.guild

        # Register views before posting them
        bot.add_view(RaidsView(guild))
        bot.add_view(BossesView(guild))
        bot.add_view(EventsView(guild))

        print("🔄 Purging and reposting role assignment panels...")
        async for msg in role_channel.history(limit=100):
            if msg.author == bot.user:
                await msg.delete()

        await role_channel.send("Select your roles below:")

        raid_embed = discord.Embed(title="⚔︎ ℜ𝔞𝔦𝔡𝔰 ⚔︎", description="", color=0x00ff00)
        await role_channel.send(embed=raid_embed, view=RaidsView(guild))

        boss_embed = discord.Embed(title="⚔︎ 𝔊𝔯𝔬𝔲p 𝔅𝔬𝔰𝔰𝔢𝔰 ⚔︎", description="", color=0x0000ff)
        await role_channel.send(embed=boss_embed, view=BossesView(guild))

        events_embed = discord.Embed(title="⚔︎ 𝔈𝔳𝔢𝔫𝔱𝔰 ⚔︎", description="", color=0xffff00)
        await role_channel.send(embed=events_embed, view=EventsView(guild))
        print("✅ Role assignment panels reposted.")

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands.")
    except Exception as e:
        print(f"❌ Command sync failed: {e}")

# ---------------------------
# 🔹 Run Bot
# ---------------------------
bot.run(os.getenv('DISCORD_BOT_TOKEN'))


