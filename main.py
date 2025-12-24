import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import asyncio
import re
from discord.ui import Modal, TextInput, View, Button
from discord import ButtonStyle
from typing import Optional
from datetime import datetime, timedelta, timezone, time
from zoneinfo import ZoneInfo
import aiohttp
import random
import urllib.parse
import requests

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

MENTOR_ROLE_ID = 1306021911830073414
SANG_ROLE_ID = 1387153629072592916
TOB_ROLE_ID = 1272694636921753701
EVENTS_ROLE_ID = 1298358942887317555
GUILD_ID = 1272629330115297330 # <-- Added your Guild ID for command syncing

# --- Justice Panel Config ---
JUSTICE_PANEL_CHANNEL_ID = 1422373286368776314 # Channel where the main panel will be.
SENIOR_STAFF_CHANNEL_ID = 1336473990302142484  # Channel for approval notifications.
ADMINISTRATOR_ROLE_ID = 1272961765034164318    # Role that can approve actions.
SENIOR_STAFF_ROLE_ID = 1336473488159936512    # Role that can approve actions.
INACTIVE_ROLE_ID = 1392889183265230848         # Role for inactive members

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
        ("Rule 4️⃣ - No Rage-Quitting Raids/Bosses", "Angrily leaving/\"rage quitting\" raids mid-raid and bosses mid-trip is frowned upon and not welcome here, and will often result in a warning. You wouldn't like it if it happened to you, so please don't do it to others. We ask that you continue the raid when possible and peacefully let others know you would prefer not to do another."),
        ("Rule 5️⃣ - Don’t Share Others' Personal Information", "You are welcome to share your own personal information, but sharing other people’s personal information without consent will result in a warning if it's light enough or a possible ban. Trust is important, and breaking it with people in our community, or with friends, will make you unwelcome in the clan."),
        ("Rule 6️⃣ - No Sharing or Using Plug-ins from Unofficial Clients", "Cheat plug-ins or plug-ins aimed at scamming others through downloads are not allowed, both in-game and on a Discord. These plug-ins are often dangerous and can lead to being banned if undeniable proof is given to us."),
        ("Rule 7️⃣ - No Scamming, Luring, or Begging", "Social engineering, scamming, and luring will result in a RuneWatch case and a ban from the clan, whether it happens to people inside or outside of the clan.\nBegging is extremely irritating and will result in a warning."),
        ("Rule 8️⃣ - All Uniques Must Be Split", "Any unique obtained in group content **must be split** unless stated otherwise before the raid and **agreed upon by all members - This includes members joining your raid**.\nYou also need to split loot with your team members (who are in the clan) **even if** you are doing content on an FFA world, in an FFA clan chat, or if you are an Ironman."),
        ("Rule 9️⃣ - You Must Have Your In-Game Name Set As Your Discord Name", "In order to keep track of clan members during events and reach out to you, you **MUST** have your Discord nickname include your in-game name.\n\n**Acceptable Formats:**\n✅ `- Discord Name / In-Game Name`\n✅ `- Discord Name (In-Game Name)`\n✅ `- In-Game Name Only`\n❌ `- Discord Name Only`\n\n**Enforcement:**\n*We will attempt to replace your name for you, but may reach out if we do not find an in-game match. If you do not reply, you may be mistakenly removed from the Discord.*")
    ]

    rule_colors = [
        (206, 2, 2), (201, 4, 4), (195, 5, 5), (190, 6, 6),
        (185, 7, 7), (179, 9, 9), (174, 10, 10), (168, 12, 12), (168, 12, 12)
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
   
    await interaction.channel.send("https://i.postimg.cc/qgfnZ0Pq/img.png")
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
✦ 2376 total level
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
@app_commands.checks.has_any_role("Clan Staff")
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

    # This section will now also include commands from your cog
    embed.add_field(
        name="🩸 Sanguine Sunday (ToB)",
        value="""
        `/sangmatch` - 🔒 (Staff) Create ToB teams from signups in a voice channel.
        `/sangmatchtest` - 🔒 (Staff) Create ToB teams without pings or creating VCs.
        `/sangsignup` - 🔒 (Staff) Manually post the Sanguine Sunday signup or reminder message.
        `/sangexport` - 🔒 (Staff) Export the most recently generated teams to a text file.
        `/sangcleanup` - 🔒 (Staff) Delete auto-created SanguineSunday voice channels.
        """,
        inline=False
    )

    embed.add_field(
        name="🔒 Other Staff Commands",
        value="""
        `/info` - Posts the detailed clan information embeds in the current channel.
        `/rules` - Posts the clan rules embeds in the current channel.
        `/rank` - Posts the rank requirement embeds in the current channel.
        `/say [message]` - Makes the bot send the specified message in the current channel.
        `/welcome` - (Used in ticket threads) Welcomes a new member and assigns default roles.
        `/rsn_panel` - Posts the interactive RSN registration panel.
        `/time_panel` - Posts the interactive timezone selection panel.
        `/justice_panel` - 🔒 (Staff) Posts the server protection panel.
        `/support_panel` - 🔒 (Staff) Posts the staff support specialty role selector.
        """,
        inline=False
    )

    embed.set_footer(text="Use the commands in the appropriate channels. Contact staff for any issues.")

    await interaction.followup.send(embed=embed, ephemeral=True)

# ---------------------------
# 🔹 Welcome
# ---------------------------
class WelcomeView(View):
    def __init__(self):
        super().__init__(timeout=None)

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

        await interaction.response.send_message(feedback, ephemeral=True)
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
        self.add_item(RoleButton("Barb Assault", get_emoji("ba")))
        self.add_item(RoleButton("Events", get_emoji("event")))
        self.add_item(RoleButton("Boss of the Week", get_emoji("botw")))
        self.add_item(RoleButton("Skill of the Week", get_emoji("sotw")))
        self.add_item(RoleButton("Sanguine Sunday - Learn ToB!", get_emoji("sanguine_sunday")))
        self.add_item(RoleButton("PvP", "💀"))

class CloseThreadView(View):
    """A view with a single button to close a support thread."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, custom_id="close_support_thread")
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

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success)
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

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger)
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
        super().__init__(label=role_name, style=discord.ButtonStyle.secondary, emoji=emoji, custom_id=f"support_ticket_{role_name.replace(' ', '_')}")

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
        cell = rsn_sheet.find(member_id)
        rsn_value = rsn_sheet.cell(cell.row, 4).value
        await interaction.response.send_message(
            f"✅ Your registered RSN is **{rsn_value}**.",
            ephemeral=True
        )
    except gspread.exceptions.CellNotFound:
        await interaction.response.send_message(
            "⚠️ You have not registered an RSN yet. Use /rsn_panel to register.",
            ephemeral=True
        )


@rsn_panel.error
async def rsn_panel_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.errors.MissingAnyRole):
        await interaction.response.send_message(
            "⛔ You do not have permission to use this command.",
            ephemeral=True
        )

CLOG_LINE_INDEX = 44

@bot.tree.command(name="clog", description="Check the Collection Log count for an OSRS player")
@app_commands.describe(username="The OSRS username to check")
async def clog(interaction: discord.Interaction, username: str):
    await interaction.response.defer()

    safe_username = username.replace(" ", "%20")
    url = f"https://secure.runescape.com/m=hiscore_oldschool/index_lite.ws?player={safe_username}"

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 404:
            await interaction.followup.send(f"❌ User **{username}** not found on the Hiscores.")
            return
        
        if response.status_code != 200:
            await interaction.followup.send(f"⚠️ API Error (Status {response.status_code}). Jagex servers might be down.")
            return

        lines = response.text.strip().split('\n')
        
        if len(lines) <= CLOG_LINE_INDEX:
             await interaction.followup.send("⚠️ API Error: Hiscores format changed. The bot owner needs to update the index.")
             return

        clog_line = lines[CLOG_LINE_INDEX]
        parts = clog_line.split(',')
        
        if len(parts) >= 2:
            score = parts[1]
            formatted_score = f"{int(score):,}"
            
            await interaction.followup.send(f"<:clogger:1406233084311113808> **{username}** has **{formatted_score}** Collection Log slots filled!")
        else:
            await interaction.followup.send("⚠️ Error parsing the specific Collection Log line.")

    except Exception as e:
        await interaction.followup.send(f"⚠️ An unexpected error occurred: {e}")

# ---------------------------
# 🔹 Santa's Naughty or Nice List
# ---------------------------

# Exhuastive word lists for an 18+ OSRS community (No slurs/hate speech)
NAUGHTY_KEYWORDS = [
    "ban him", "touch grass", "noob", "sit", "trash", "kid", "diff", "free", 
    "pleae", "rat", "gf", "ez", "garbage", "get good", "gtfo", "idiot", "loser", 
    "dumb", "moron", "washed", "hardstuck", "thrower", "mald", "seethe", "cope", 
    "clown", "dogwater", "bot", "boosted", "cleared", "planked", "hop", "l0l", 
    "skill issue", "shitter", "shit", "fuck", "hell", "damn", "ass", "pissed", 
    "stfu", "wanker", "prick", "dick", "bastard", "bitch", "crap", "bloody", 
    "piss", "bollocks"
]

NICE_KEYWORDS = [
    "sorry", "sorry about what happened", "apologies", "apologize", "my bad",
    "so handsome", "neat", "everyone's welcome", "come along", "gz", "grats", 
    "congrats", "congratulations", "nice", "gl", "hf", "huge", "beast", "clean", 
    "pog", "poggers", "ty", "thanks", "thx", "lfg", "lets go", "cracked", 
    "insane", "amazing", "big loot", "spooned", "vouch", "unreal", "help", 
    "teach", "well done", "good job", "gj", "proud", "keep it up", "carry", 
    "mentor", "guide", "tips", "share", "split", "happy to help", "no problem", 
    "np", "nw", "you're welcome", "welcome", "legend", "champion"
]

@tree.command(name="santalist", description="Determines a user's status by balancing naughty vs. nice words in their history.")
@app_commands.describe(member="The user to check (defaults to you if left blank)")
async def santalist(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    """Calculates the balance of sentiment and picks a random example from the dominant category."""
    # Defer response to handle the API time required to scan message history
    await interaction.response.defer(thinking=True)
    
    target = member or interaction.user
    naughty_matches = []
    nice_matches = []

    # Scan history with a limit of 500 to capture 100 messages from the specific user
    user_msg_count = 0
    async for message in interaction.channel.history(limit=500):
        if message.author == target:
            user_msg_count += 1
            content_lower = message.content.lower()

            # Check for and collect naughty matches
            if any(word in content_lower for word in NAUGHTY_KEYWORDS):
                naughty_matches.append(message.content)
            
            # Check for and collect nice matches
            if any(word in content_lower for word in NICE_KEYWORDS):
                nice_matches.append(message.content)
            
            # Stop once we have analyzed 100 messages from the target user
            if user_msg_count >= 100:
                break

    # Determine status based on the volume of each category
    naughty_count = len(naughty_matches)
    nice_count = len(nice_matches)

    # Comparison Logic: If counts are equal, the user is neutral
    if naughty_count > nice_count:
        # User is Naughty: Select a random example from their naughty posts
        selected_msg = random.choice(naughty_matches)
        await interaction.followup.send(
            f"{target.mention} has been naughty! 😈 (Score: {naughty_count} Naughty vs {nice_count} Nice)\n"
            f"> \"{selected_msg}\"\n"
            "Go shovel coal, you bad little elf ⚫"
        )
    elif nice_count > naughty_count:
        # User is Nice: Select a random example from their nice posts
        selected_msg = random.choice(nice_matches)
        await interaction.followup.send(
            f"{target.mention} has been nice! 🎅 (Score: {nice_count} Nice vs {naughty_count} Naughty)\n"
            f"> \"{selected_msg}\"\n"
            "Have a cookie! 🍪"
        )
    else:
        # Neutral status if counts are equal or no keywords were found
        await interaction.followup.send(
            f"I scanned 100 messages and found {naughty_count} Naughty and {nice_count} Nice words. "
            f"{target.display_name} is perfectly balanced... for now. 👀"
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

# Define which timezones use the D/M/YYYY format
INTERNATIONAL_TIMEZONES = {
    "GMT", "CET", "EET", "BRT", "ART", "AWST", "ACST", "AEST"
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
        elif entry_type == "withdraw":
            total -= amount

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


from discord.ui import Modal, TextInput, View, Button
from typing import Optional
# (Make sure other imports like discord, os, etc. are at the top of your file)

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

async def get_original_message_actors(interaction: discord.Interaction) -> tuple[Optional[discord.Message], Optional[discord.Member], Optional[discord.Member]]:
    """Helper to fetch the original post and its key actors. Mentioned user can be None."""
    try:
        if not interaction.message.reference:
            await interaction.response.send_message("❌ Button error: Cannot find original message reference.", ephemeral=True)
            return None, None, None

        original_message = await interaction.channel.fetch_message(interaction.message.reference.message_id)
        author = original_message.author
        
        mentioned_user = None
        for mention in original_message.mentions:
            if isinstance(mention, (discord.Member, discord.User)):
                mentioned_user = mention
                break 
        
        return original_message, author, mentioned_user
    
    except discord.NotFound:
        await interaction.response.send_message(f"❌ Could not find the original message (it may have been deleted).", ephemeral=True)
        return None, None, None
    except discord.Forbidden:
            await interaction.response.send_message(f"❌ I don't have permissions to read this channel's history.", ephemeral=True)
            return None, None, None
    except Exception as e:
        await interaction.response.send_message(f"❌ An unknown error occurred while fetching message details.", ephemeral=True)
        print(f"Error in get_original_message_actors: {e}")
        return None, None, None


class CollatButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Request Item", style=discord.ButtonStyle.primary, emoji="🔔", custom_id="collat:request_persistent")
    async def request_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        original_message, author, mentioned = await get_original_message_actors(interaction)
        if not original_message:
            return # Error already sent by helper

        if not (interaction.user == author or (mentioned and interaction.user == mentioned)):
            await interaction.response.send_message("You are not allowed to interact with this post.", ephemeral=True)
            return

        if not mentioned:
            await interaction.response.send_modal(CollatRequestModal(original_message, interaction.user))
            return

        target = mentioned if interaction.user == author else author 

        await interaction.response.defer()
        try:
            await original_message.reply(
                f"{interaction.user.mention} is requesting their item from {target.mention}.",
                mention_author=True
            )
        except Exception as e:
            print(f"Error trying to send collat reply: {e}")
            if not interaction.is_done():
                await interaction.followup.send(f"❌ Failed to send reply ping. Error: {e}", ephemeral=True)

    @discord.ui.button(label="Item Returned", style=discord.ButtonStyle.success, emoji="📥", custom_id="collat:returned_persistent")
    async def item_returned(self, interaction: discord.Interaction, button: discord.ui.Button):
        original_message, author, mentioned = await get_original_message_actors(interaction)
        if not original_message:
            return # Error already sent
        
        if not (interaction.user == author or (mentioned and interaction.user == mentioned)):
            await interaction.response.send_message("You are not allowed to interact with this post.", ephemeral=True)
            return

        for child in self.children:
            child.disabled = True
        
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("Item marked as returned. ✅", ephemeral=True)

# ---------------------------
# 🔹 Justice Panel (Server Protection)
# ---------------------------

class FinalConfirmationView(View):
    """An ephemeral view to provide a final warning before executing a kick or ban."""
    def __init__(self, original_message: discord.Message, initiator: discord.Member, approver: discord.Member, target: discord.Member, action: str, reason: str):
        super().__init__(timeout=60) # Short timeout for a quick decision
        self.original_message = original_message
        self.initiator = initiator
        self.approver = approver
        self.target = target
        self.action = action
        self.reason = reason

    async def update_original_message(self, status: str, color: discord.Color):
        """Updates the embed in the senior staff channel."""
        embed = self.original_message.embeds[0]
        embed.title = f"⚖️ Action {status}: {self.action.capitalize()}"
        embed.color = color
        embed.clear_fields() # Remove old fields
        embed.add_field(name="Target User", value=self.target.mention, inline=False)
        embed.add_field(name="Initiated By", value=self.initiator.mention, inline=True)
        embed.add_field(name="Handled By", value=self.approver.mention, inline=True)
        embed.add_field(name="Reason", value=self.reason, inline=False)
        embed.set_footer(text=f"This request is now closed.")
        await self.original_message.edit(embed=embed, view=None) # Remove buttons

    @discord.ui.button(label="YES, Execute Action", style=discord.ButtonStyle.danger)
    async def confirm_button(self, interaction: discord.Interaction, button: Button):
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        try:
            if self.action == "kick":
                await self.target.kick(reason=f"Action by {self.initiator.name}, approved by {self.approver.name}. Reason: {self.reason}")
            elif self.action == "ban":
                await self.target.ban(reason=f"Action by {self.initiator.name}, approved by {self.approver.name}. Reason: {self.reason}")

            # Update the original message in senior staff chat
            await self.update_original_message("Completed", discord.Color.green())
            await interaction.response.edit_message(content=f"✅ Successfully **{self.action}ed** {self.target.name}.", view=None)

            # Send log message
            if log_channel:
                log_embed = discord.Embed(
                    title=f"Moderation Action: {self.action.capitalize()}",
                    color=discord.Color.red() if self.action == "ban" else discord.Color.orange(),
                    timestamp=datetime.now()
                )
                log_embed.add_field(name="Target User", value=f"{self.target.name} ({self.target.id})", inline=False)
                log_embed.add_field(name="Initiated By", value=f"{self.initiator.name} ({self.initiator.id})", inline=True)
                log_embed.add_field(name="Approved By", value=f"{self.approver.name} ({self.approver.id})", inline=True)
                log_embed.add_field(name="Reason", value=self.reason, inline=False)
                await log_channel.send(embed=log_embed)

        except discord.Forbidden:
            await interaction.response.edit_message(content="❌ **Action Failed.** I don't have the necessary permissions to perform this action.", view=None)
            await self.update_original_message("Failed (Permissions)", discord.Color.dark_grey())
        except Exception as e:
            await interaction.response.edit_message(content=f"An unexpected error occurred: {e}", view=None)
            await self.update_original_message("Failed (Error)", discord.Color.dark_grey())

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(content="Action cancelled.", view=None)


class ApprovalView(View):
    """The view sent to Senior Staff with Approve/Deny buttons."""
    def __init__(self, initiator: discord.Member, target: discord.Member, action: str, reason: str):
        super().__init__(timeout=None) # Persists until manually handled
        self.initiator = initiator
        self.target = target
        self.action = action
        self.reason = reason

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Checks if the user has the required role to approve or deny."""
        approver_roles = {role.id for role in interaction.user.roles}
        if not {ADMINISTRATOR_ROLE_ID, SENIOR_STAFF_ROLE_ID}.intersection(approver_roles):
            await interaction.response.send_message("❌ You do not have the required role to handle this request.", ephemeral=True)
            return False
        if interaction.user.id == self.initiator.id:
            await interaction.response.send_message("❌ You cannot approve or deny your own request.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success)
    async def approve_button(self, interaction: discord.Interaction, button: Button):
        final_view = FinalConfirmationView(
            original_message=interaction.message,
            initiator=self.initiator,
            approver=interaction.user,
            target=self.target,
            action=self.action,
            reason=self.reason
        )
        await interaction.response.send_message(
            f"⚠️ **Final Warning** ⚠️\nAre you sure you want to **{self.action.upper()}** the user {self.target.name}?",
            view=final_view,
            ephemeral=True
        )

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.danger)
    async def deny_button(self, interaction: discord.Interaction, button: Button):
        embed = interaction.message.embeds[0]
        embed.title = f"⚖️ Action Denied: {self.action.capitalize()}"
        embed.color = discord.Color.red()
        embed.clear_fields()
        embed.add_field(name="Target User", value=self.target.mention, inline=False)
        embed.add_field(name="Initiated By", value=self.initiator.mention, inline=True)
        embed.add_field(name="Denied By", value=interaction.user.mention, inline=True)
        embed.add_field(name="Reason", value=self.reason, inline=False)
        embed.set_footer(text="This request has been denied and is now closed.")

        await interaction.response.edit_message(embed=embed, view=None)

@bot.tree.command(name="support_panel", description="Posts the staff support specialty role selector.")
@app_commands.checks.has_any_role("Administrators")
async def support_panel(interaction: discord.Interaction):
    channel = bot.get_channel(SUPPORT_PANEL_CHANNEL_ID)
    if not channel:
        await interaction.response.send_message("❌ Support panel channel not found. Please set it in the config.", ephemeral=True)
        return

    await send_support_panel(channel)
    await interaction.response.send_message(f"✅ Support specialty panel posted in {channel.mention}.", ephemeral=True)

class JusticeActionModal(Modal):
    target_user = TextInput(label="User's Name or ID", placeholder="Enter the exact username or user ID.", required=True)
    reason = TextInput(label="Reason", style=discord.TextStyle.paragraph, placeholder="Provide a detailed reason for this action.", required=True)

    def __init__(self, action: str):
        super().__init__(title=f"Initiate User {action.capitalize()}")
        self.action = action

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        target_str = self.target_user.value
        target = None
        try:
            target_id = int(target_str)
            target = interaction.guild.get_member(target_id)
        except ValueError:
            target = discord.utils.get(interaction.guild.members, name=target_str)

        if not target:
            await interaction.followup.send(f"❌ Could not find a user with the name or ID: {target_str}.", ephemeral=True)
            return

        # Post Confirmation Message to Senior Staff Channel
        senior_staff_channel = bot.get_channel(SENIOR_STAFF_CHANNEL_ID)
        if not senior_staff_channel:
            await interaction.followup.send("❌ Senior Staff channel not found. Please configure the bot.", ephemeral=True)
            return

        emoji = "🥊" if self.action == "ban" else "🥾"
        embed = discord.Embed(
            title=f"{emoji} Moderation Request: {self.action.capitalize()}",
            description="A staff member has requested to take action. This requires approval from Senior Staff or an Administrator.",
            color=discord.Color.yellow()
        )
        embed.add_field(name="Target User", value=target.mention, inline=False)
        embed.add_field(name="Initiated By", value=interaction.user.mention, inline=False)
        embed.add_field(name="Reason", value=self.reason.value, inline=False)
        embed.set_footer(text="Please review carefully before taking action.")

        view = ApprovalView(initiator=interaction.user, target=target, action=self.action, reason=self.reason.value)

        await senior_staff_channel.send(embed=embed, view=view)
        await interaction.followup.send(f"✅ Your request to **{self.action} {target.name}** has been sent to Senior Staff for approval.", ephemeral=True)


class JusticePanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Initiate Kick", style=discord.ButtonStyle.secondary, custom_id="initiate_kick", emoji="🥾")
    async def initiate_kick(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(JusticeActionModal("kick"))

    @discord.ui.button(label="Initiate Ban", style=discord.ButtonStyle.danger, custom_id="initiate_ban", emoji="🥊")
    async def initiate_ban(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(JusticeActionModal("ban"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Checks if the user has the Clan Staff role."""
        # Using STAFF_ROLE_ID from your config as the intended role
        staff_role = discord.utils.get(interaction.guild.roles, id=STAFF_ROLE_ID) 
        if staff_role and staff_role in interaction.user.roles:
            return True
        # Check for the other ID just in case it was intended
        other_staff_role = discord.utils.get(interaction.guild.roles, id=1431045433798688768)
        if other_staff_role and other_staff_role in interaction.user.roles:
            return True
        await interaction.response.send_message("❌ This panel is for Clan Staff members only.", ephemeral=True)
        return False


@bot.tree.command(name="justice_panel", description="Posts the server protection panel.")
@app_commands.checks.has_any_role("Administrators")
async def justice_panel(interaction: discord.Interaction):
    channel = bot.get_channel(JUSTICE_PANEL_CHANNEL_ID)
    if not channel:
        await interaction.response.send_message("❌ Justice panel channel not found. Please set it in the config.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🛡️ Justice Panel 🛡️",
        description=(
            "This panel serves as a server protection system. It allows Trial Staff to request the removal of a user, subject to approval.\n\n"
            "**Instructions for Trial Staff:**\n"
            "1. Click **Initiate Kick** or **Initiate Ban**.\n"
            "2. Fill out the user's **exact name or ID** and a **detailed reason**.\n"
            "3. A request will be sent to the Senior Staff channel for approval.\n\n"
            "*All actions are logged for transparency.*"
        ),
        color=discord.Color.dark_blue()
    )
    await channel.send(embed=embed, view=JusticePanelView())
    await interaction.response.send_message(f"✅ Justice panel posted in {channel.mention}.", ephemeral=True)

# ---------------------------
# 🔹 Bot Events
# ---------------------------

@bot.event
async def on_message(message: discord.Message):
    global message_counter, translation_threshold
    
    if message.author.bot:
        return

    await bot.process_commands(message)

    parent_channel_id = None
    if isinstance(message.channel, discord.Thread):
        parent_channel_id = message.channel.parent.id
    elif isinstance(message.channel, discord.TextChannel):
        parent_channel_id = message.channel.id

    if message.channel.id == COLLAT_CHANNEL_ID:
        has_pasted_image = any(embed.image for embed in message.embeds)
        is_reply = message.reference is not None

        if (message.attachments or has_pasted_image) and not is_reply:
            view = CollatButtons() # Stateless view
            await message.reply("Collat actions:", view=view, allowed_mentions=discord.AllowedMentions.none())

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    """Sends a DM to a user when they receive the Inactive role."""
    if after.bot:
        return

    if before.roles == after.roles:
        return

    roles_added = set(after.roles) - set(before.roles)

    inactive_role = discord.utils.get(after.guild.roles, id=INACTIVE_ROLE_ID)

    if inactive_role and inactive_role in roles_added:
        message_content = (
            f"Hey {after.display_name}! :wave:\n\n"
            "We noticed you haven't been active in a while, so we've marked you as 'inactive' to clean up our member list. "
            "No hard feelings at all, this is just routine housekeeping!\n\n"
            "Want to come back? :handshake:\n"
            "There's no need to re-apply. Just head to https://discord.com/channels/1272629330115297330/1272648453264248852 and use the 'Returning Player' button, "
            "and a staff member will get you a re-invite in-game when you're on.\n\n"
            "Hope to see you again soon!"
        )

        try:
            await after.send(message_content)
            print(f"Sent inactivity DM to {after.name}")
        except discord.Forbidden:
            print(f"❌ Could not send inactivity DM to {after.name}. They may have DMs disabled.")
        except Exception as e:
            print(f"❌ An error occurred while sending inactivity DM to {after.name}: {e}")

has_synced = False

@bot.event
async def on_ready():
    global has_synced
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

    if not has_synced:
        try:
            guild = discord.Object(id=GUILD_ID)
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"✅ Synced {len(synced)} commands to the guild.")
            has_synced = True
        except Exception as e:
            print(f"❌ Command sync failed: {e}")

    print("Main bot components are ready.")

    bot.add_view(JusticePanelView())
    bot.add_view(SupportRoleView())
    bot.add_view(RSNPanelView())
    bot.add_view(CloseThreadView())
    bot.add_view(CollatButtons())
    
    # Add persistent views for role panels
    if bot.get_channel(1272648586198519818): # Check if role_channel exists
        guild = bot.get_guild(GUILD_ID)
        if guild:
            bot.add_view(RaidsView(guild))
            bot.add_view(BossesView(guild))
            bot.add_view(EventsView(guild))          
    # Add persistent view for timezone panel
    if bot.get_channel(1398775387139342386):
        guild = bot.get_guild(GUILD_ID)
        if guild:
            bot.add_view(TimezoneView(guild))


    asyncio.create_task(rsn_writer())

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
        print("🔄 Purging and reposting role assignment panels...")

        # Purge old messages from the bot
        try:
            async for msg in role_channel.history(limit=50):
                if msg.author == bot.user:
                    await msg.delete()
        except discord.Forbidden:
            print("❌ Bot lacks permission to delete messages in the role channel.")
        except Exception as e:
            print(f"❌ Error purging role channel: {e}")

        await role_channel.send("https://i.postimg.cc/8G3CWSDP/info.png") # Banner

        await role_channel.send(
            "Select your roles below to get pings for group content and events!",
            allowed_mentions=discord.AllowedMentions.none()
            )

        raid_embed = discord.Embed(title="⚔︎ ℜ𝔞𝔦d𝔰 ⚔︎", description="Roles for Chambers of Xeric, Theatre of Blood, and Tombs of Amascut.", color=0xDAA520)
        await role_channel.send(embed=raid_embed, view=RaidsView(guild))

        boss_embed = discord.Embed(title="⚔︎ 𝔊𝔯𝔬𝔲p B𝔬𝔰𝔰𝔢𝔰 ⚔︎", description="Roles for God Wars Dungeon, Corporeal Beast, and more.", color=0xC0C0C0)
        await role_channel.send(embed=boss_embed, view=BossesView(guild))

        events_embed = discord.Embed(title="⚔︎ 𝔈𝔳𝔢𝔫𝔱s/𝔐𝔦𝔫𝔦𝔤𝔞𝔪𝔢𝔰 ⚔︎", description="Roles for clan events, skill/boss of the week, and PvP.", color=0xCD7F32)
        await role_channel.send(embed=events_embed, view=EventsView(guild))
        print("✅ Role assignment panels reposted.")


async def main():
    async with bot:
        cogs_to_load = ["sanguine_cog", "Rancour"]
        for cog_name in cogs_to_load:
            try:
                await bot.load_extension(cog_name)
                print(f"✅ Successfully loaded extension: {cog_name}")
            except Exception as e:
                print(f"🔥 Failed to load extension {cog_name}.")
                print(f"  Error: {e}")

        bot_token = os.getenv('DISCORD_BOT_TOKEN')
        if not bot_token:
            print("❌ DISCORD_BOT_TOKEN environment variable not set.")
            return
        await bot.start(bot_token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot is shutting down...")	
