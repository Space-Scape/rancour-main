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
        title="1️⃣ What We Offer",
        description="""➤ PvM of all levels
        ➤ Skilling and Bossing Competitions
        ➤ Raids - and learner friendly raids
        ➤ Games/Bingos - win huge prizes
        ➤ Social Events - come and hang out!
        ➤ ToB Learner Events - hosted by MacFlag
        ➤ Mentoring - happy to assist""",
        color=discord.Color.from_rgb(195, 238, 238)
    )
    await interaction.channel.send(embed=offer_embed)
    await asyncio.sleep(0.5)

    # --- Requirements Embed ---
    requirements_embed = discord.Embed(
        title="2️⃣ Our Requirements",
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
        color=discord.Color.from_rgb(206, 227, 227)
    )
    await interaction.channel.send(embed=requirements_embed)
    await asyncio.sleep(0.5)

    # --- Systems Embed ---
    systems_embed = discord.Embed(
        title="3️⃣ Clan Ticket Systems and Name Changing",
        description="""<#1272648453264248852> - Welcome!

        <#1272648472184487937> - Update your ranks here.

        <#1272648498554077304> - Report rule-breaking or bot failures, get private help, make suggestions, and more!

        <#1280532494139002912> - Use this for name changes.

        Guests are always welcome to hang out and get a feel for our community before becoming a member. Just ask!""",
        color=discord.Color.from_rgb(217, 216, 216)
    )
    await interaction.channel.send(embed=systems_embed)
    await asyncio.sleep(0.5)

    # --- Key Channels & Roles Embed ---
    key_channels_embed = discord.Embed(
        title="4️⃣ Key Channels & Roles",
        description="""<#1272648586198519818> - assign roles to get pings for bosses, raids, and events.

        <#1272648555772776529> - Looking for a group?

        <#1272646577432825977> - Check out all upcoming clan events.

        <#1272629331524587624> - Share your drops and level-ups.

        <:mentor:1406802212382052412> **Mentoring:** After two weeks and earning the <:corporal:1406217420187893771> rank, you can open a mentor ticket for PVM guidance. Experienced players can apply to become a mentor in <#1272648472184487937>.""",
        color=discord.Color.from_rgb(228, 205, 205)
    )
    await interaction.channel.send(embed=key_channels_embed)
    await asyncio.sleep(0.5)

    # --- More Channels & Bots Embed ---
    more_channels_embed = discord.Embed(
        title="5️⃣ More Channels & Bots",
        description="""<#1272648340940525648> - For item trades. Post a screenshot and @mention a user to bring up `Request Item` & `Item Returned` buttons.
 Requesting pings a user, and Returning locks the buttons.

 <#1272875477555482666> - A real-time feed of the in-game clan chat.

 <#1420951302841831587> - A drop leaderboard and clan-wide loot tracker (instructions here: https://discord.com/channels/1272629330115297330/1272646547020185704/1421015420160184381)

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
        title="6️⃣ Timezones & Active Hours",
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
@app_commands.checks.has_any_role("Moderators")
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
        description="""✦ 20+ Pets
        ✦ Meets Sergeant Requirements""",
        color=discord.Color.from_rgb(180, 45, 45)
    )
    await interaction.channel.send(embed=pet_hunter_embed)
    await asyncio.sleep(0.5)

    # --- Clogger Embed ---
    clogger_embed = discord.Embed(
        title="Clogger - <:clogger:1406233084311113808>",
        description="""✦ 1000+ Collection Log Slots
        ✦ Meets Sergeant Requirements""",
        color=discord.Color.from_rgb(160, 40, 40)
    )
    await interaction.channel.send(embed=clogger_embed)
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
        `/addevent` - Opens a modal to add a new event to the clan schedule.
        `/schedule` - Manually posts the daily event schedule.
        """,
        inline=False
    )

    embed.set_footer(text="Use the commands in the appropriate channels. Contact staff for any issues.")

    await interaction.followup.send(embed=embed, ephemeral=True)

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
        
# --------------------------------------------------
# 🔹 Event Management System
# --------------------------------------------------

def get_all_event_records():
    """Custom function to get all event records, accounting for header row at row 4."""
    try:
        all_values = events_sheet.get_all_values()
        if len(all_values) < 5:
            return []
        
        headers = all_values[3]
        data_rows = all_values[4:]
        
        records = []
        for row in data_rows:
            record = {headers[i]: (row[i] if i < len(row) else "") for i in range(len(headers))}
            if any(val.strip() for val in record.values()):
                records.append(record)
        return records
    except Exception as e:
        print(f"Error fetching and parsing event sheet data: {e}")
        return []

def parse_flexible_date(date_string: str) -> Optional[datetime.date]:
    """Tries to parse a date from a few common formats."""
    formats_to_try = ["%m/%d/%Y", "%m/%d/%y", "%-m/%-d/%Y", "%-m/%-d/%y"]
    for fmt in formats_to_try:
        try:
            return datetime.strptime(date_string.strip(), fmt).date()
        except ValueError:
            continue
    return None

class AddEventModal(Modal):
    def __init__(self, event_type: str):
        super().__init__()
        self.event_type = event_type
        self.title = f"Create New '{event_type}' Event"

    event_description = TextInput(
        label="Event Description",
        placeholder="e.g., Learner ToB or Barb Assault",
        required=True
    )
    start_date = TextInput(
        label="Start Date (e.g., 9/29/2025)",
        placeholder="Use MM/DD/YYYY format.",
        required=True
    )
    end_date = TextInput(
        label="End Date (Optional)",
        placeholder="Leave blank for single-day events.",
        required=False
    )
    comments = TextInput(
        label="Comments (Optional)",
        style=discord.TextStyle.paragraph,
        placeholder="e.g., Hosted by X, design by Y",
        required=False
    )
    helpers_co_hosts = TextInput(
        label="Helpers/Co-Hosts (Optional)",
        style=discord.TextStyle.short,
        placeholder="Comma-separated names, e.g., Riolu, Macflag",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # 1. Date Validation and Parsing
        start_date_obj = parse_flexible_date(self.start_date.value)
        if not start_date_obj:
            await interaction.followup.send("❌ **Invalid Start Date.** Please use a valid format like **9/29/2025**.", ephemeral=True)
            return

        end_date_obj = start_date_obj
        if self.end_date.value:
            end_date_obj = parse_flexible_date(self.end_date.value)
            if not end_date_obj:
                await interaction.followup.send("❌ **Invalid End Date.** Please use a valid format like **9/29/2025**.", ephemeral=True)
                return

        if end_date_obj < start_date_obj:
            await interaction.followup.send("❌ **Date Error.** The end date cannot be before the start date.", ephemeral=True)
            return

        start_date_str = start_date_obj.strftime("%m/%d/%Y")
        end_date_str = end_date_obj.strftime("%m/%d/%Y")
        
        # 2. Check for Conflicting Events
        conflicting_events_details = []
        weekly_event_types_to_ignore = ["pet roulette", "sanguine sunday", "botw", "sotw", "boss of the week", "skill of the week"]
        try:
            all_events = get_all_event_records()
            for event in all_events:
                if event.get("Type of Event", "").strip().lower() in weekly_event_types_to_ignore:
                    continue

                existing_start_str = event.get("Start Date")
                existing_end_str = event.get("End Date")
                if not existing_start_str or not existing_end_str: continue

                existing_start_obj = parse_flexible_date(existing_start_str)
                existing_end_obj = parse_flexible_date(existing_end_str)
                if not existing_start_obj or not existing_end_obj: continue

                if max(start_date_obj, existing_start_obj) <= min(end_date_obj, existing_end_obj):
                    detail = f"- **{event.get('Event Description', 'N/A')}**・Hosted by {event.get('Event Owner', 'N/A')}"
                    conflicting_events_details.append(detail)
        except Exception as e:
            print(f"Could not fetch event records for conflict check: {e}")

        # 3. Data Preparation and Writing to Sheet
        event_owner = interaction.user.display_name
        event_data = [
            self.event_type,
            self.event_description.value,
            event_owner,
            f"'{start_date_str}", # Prepend ' to force literal string
            f"'{end_date_str}",
            self.comments.value or ""
        ]

        try:
            events_sheet.append_row(event_data, value_input_option='USER_ENTERED')
            
            # Handle Helpers/Co-Hosts
            if self.helpers_co_hosts.value:
                helper_names = [name.strip() for name in self.helpers_co_hosts.value.split(',') if name.strip()]
                for name in helper_names:
                    helper_data = event_data.copy()
                    helper_data[2] = name
                    helper_data[5] = "Helper/Co-Host"
                    events_sheet.append_row(helper_data, value_input_option='USER_ENTERED')

            # 4. Public Announcement and Private Confirmation
            event_channel = bot.get_channel(EVENT_SCHEDULE_CHANNEL_ID)
            if event_channel:
                announce_embed = discord.Embed(
                    title=f"🗓️ New Event Added: {self.event_description.value}",
                    description=f"A new **{self.event_type}** has been added to the schedule!",
                    color=discord.Color.blue()
                )
                announce_embed.add_field(name="Host", value=event_owner, inline=True)
                date_display = start_date_str if start_date_str == end_date_str else f"{start_date_str} to {end_date_str}"
                announce_embed.add_field(name="Date(s)", value=date_display, inline=True)
                if self.comments.value:
                    announce_embed.add_field(name="Details", value=self.comments.value, inline=False)
                
                await event_channel.send(embed=announce_embed)

            confirm_embed = discord.Embed(
                title="✅ Event Created Successfully!",
                description="The event has been added and a notification has been posted.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=confirm_embed, ephemeral=True)

            if conflicting_events_details:
                await interaction.followup.send(
                    f"⚠️ **Heads up!** You've scheduled on the same day as another event:\n" + "\n".join(conflicting_events_details),
                    ephemeral=True
                )
        except Exception as e:
            print(f"Error writing event to sheet: {e}")
            await interaction.followup.send("❌ An error occurred while saving the event. Please check the logs.", ephemeral=True)

@bot.tree.command(name="addevent", description="Add a new event to the clan schedule.")
@app_commands.checks.has_role(STAFF_ROLE_ID)
@app_commands.describe(event_type="The type of event you want to create.")
@app_commands.choices(event_type=[
    app_commands.Choice(name="Pet Roulette", value="Pet Roulette"),
    app_commands.Choice(name="Sanguine Sunday", value="Sanguine Sunday"),
    app_commands.Choice(name="Mass Event", value="Mass Event"),
    app_commands.Choice(name="Large Event", value="Large Event"),
    app_commands.Choice(name="Other Event", value="Other Event"),
    app_commands.Choice(name="Clan Event", value="Clan Event"),
    app_commands.Choice(name="Bingo", value="Bingo"),
    app_commands.Choice(name="BOTW", value="BOTW"),
    app_commands.Choice(name="SOTW", value="SOTW"),
])
async def addevent(interaction: discord.Interaction, event_type: str):
    """Opens a modal to add the details for the chosen event type."""
    await interaction.response.send_modal(AddEventModal(event_type=event_type))

@addevent.error
async def addevent_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)

async def create_and_post_schedule(channel: discord.TextChannel):
    """Fetches, processes, and posts a clean, consolidated weekly event schedule."""
    try:
        # Run the synchronous gspread call in an executor
        all_events = await bot.loop.run_in_executor(None, get_all_event_records)
    except Exception as e:
        print(f"Could not fetch event records: {e}")
        await channel.send("⚠️ Could not retrieve event data from the spreadsheet.")
        return

    now = datetime.now(CST)
    today = now.date()
    start_of_week = today - timedelta(days=(today.weekday() + 1) % 7)
    end_of_week = start_of_week + timedelta(days=6)

    # --- 1. Pre-process and Consolidate Events ---
    regular_events = {}
    # Use the preferred shorter names for the keys and types
    weekly_events = {
        "BOTW": {"hosts": set(), "type": "BOTW"},
        "SOTW": {"hosts": set(), "type": "SOTW"},
        "Pet Roulette": {"hosts": set(), "type": "Pet Roulette"}
    }

    for event in all_events:
        owner = event.get("Event Owner", "N/A").strip()
        event_type = event.get("Type of Event", "").strip()
        description = event.get("Event Description", "").strip()

        # Use a rigid if/elif/else structure with comprehensive, case-insensitive checks.
        if event_type.lower() == "pet roulette":
            weekly_events["Pet Roulette"]["hosts"].add(owner)
        
        elif event_type.lower() in ["boss of the week", "botw"] or description.lower().startswith("botw"):
            weekly_events["BOTW"]["hosts"].add(owner)

        elif event_type.lower() in ["skill of the week", "sotw"] or description.lower().startswith("sotw"):
            weekly_events["SOTW"]["hosts"].add(owner)
            
        elif event.get("Comments", "").strip().lower() == "helper/co-host":
            continue # This is just for skipping, it's fine.

        else: # This event is a regular event
            key = (event.get("Start Date"), description)
            if key not in regular_events:
                regular_events[key] = event.copy()
                regular_events[key]["hosts"] = {owner}
            else:
                regular_events[key]["hosts"].add(owner)

    # --- 2. Populate the Weekly Schedule ---
    events_by_date = {start_of_week + timedelta(days=i): [] for i in range(7)}

    # Add regular, consolidated events to the schedule
    for event in regular_events.values():
        try:
            start_date = datetime.strptime(event["Start Date"], "%m/%d/%Y").date()
            end_date = datetime.strptime(event["End Date"], "%m/%d/%Y").date()
            
            current_date = start_date
            while current_date <= end_date:
                if start_of_week <= current_date <= end_of_week:
                    events_by_date[current_date].append(event)
                current_date += timedelta(days=1)
        except (ValueError, TypeError, KeyError):
            continue

    # Add the special weekly events ONLY on Sunday
    sunday_date = start_of_week
    for desc, data in weekly_events.items():
        if data["hosts"]:
            events_by_date[sunday_date].append({
                "Event Description": desc,
                "Type of Event": data["type"],
                "hosts": data["hosts"]
            })

    # --- 3. Build the Embed ---
    embed = discord.Embed(
        title=f"📅 Weekly Clan Schedule ({start_of_week.strftime('%b %d')} - {end_of_week.strftime('%b %d')})",
        color=discord.Color.gold()
    )

    # Build the main schedule description
    weekly_lines = ["# Events Schedule"]
    for day_index in range(7):
        current_date = start_of_week + timedelta(days=day_index)
        day_name = current_date.strftime("%A")
        weekly_lines.append(f"\n**{day_name}**")

        day_events = sorted(events_by_date[current_date], key=lambda x: x.get("Event Description", ""))
        
        if not day_events:
            weekly_lines.append("- No Event Planned.")
        else:
            for event in day_events:
                host_list = sorted(list(event.get("hosts", {"N/A"})))
                host_str = " & ".join(host_list)
                
                event_type_str = event.get('Type of Event', '').strip() or 'Other Event'
                event_desc_str = event.get('Event Description', '').strip()

                # Avoid redundancy like "Bingo: Bingo"
                if event_type_str.lower() == event_desc_str.lower():
                    line = f"- **{event_type_str}**・Hosted by {host_str}"
                else:
                    line = f"- **{event_type_str}**: {event_desc_str}・Hosted by {host_str}"
                weekly_lines.append(line)

    embed.description = "\n".join(weekly_lines)

    # Build the "Events Today" field
    todays_events = sorted(events_by_date.get(today, []), key=lambda x: x.get("Event Description", ""))
    if todays_events:
        today_lines = []
        for event in todays_events:
            host_list = sorted(list(event.get("hosts", {"N/A"})))
            host_str = " & ".join(host_list)

            event_type_str = event.get('Type of Event', '').strip() or 'Other Event'
            event_desc_str = event.get('Event Description', '').strip()

            # Avoid redundancy like "Bingo: Bingo"
            if event_type_str.lower() == event_desc_str.lower():
                line = f"- **{event_type_str}**・Hosted by {host_str}"
            else:
                line = f"- **{event_type_str}**: {event_desc_str}・Hosted by {host_str}"
            today_lines.append(line)
        
        embed.add_field(name="# Events Today #", value="\n".join(today_lines), inline=False)

    embed.set_footer(text=f"Last Updated: {now.strftime('%m/%d/%Y %I:%M %p CST')}")
    await channel.send(embed=embed)

@bot.tree.command(name="schedule", description="Posts the daily event schedule.")
@app_commands.checks.has_role(STAFF_ROLE_ID)
async def schedule(interaction: discord.Interaction):
    """Manually triggers the posting of the daily event schedule."""
    await interaction.response.defer(ephemeral=True)
    channel = bot.get_channel(EVENT_SCHEDULE_CHANNEL_ID)
    if channel:
        await create_and_post_schedule(channel)
        await interaction.followup.send(f"✅ Daily schedule posted in {channel.mention}!", ephemeral=True)
    else:
        await interaction.followup.send("⚠️ Could not find the event schedule channel.", ephemeral=True)

@schedule.error
async def schedule_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
     if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)

@tasks.loop(time=time(hour=9, minute=0, tzinfo=CST))
async def post_daily_schedule():
    """Scheduled task to post the event schedule every day at 9 AM CST."""
    channel = bot.get_channel(EVENT_SCHEDULE_CHANNEL_ID)
    if channel:
        await channel.purge(limit=5) # Clean up old schedules
        await create_and_post_schedule(channel)
        print("✅ Automatically posted the daily event schedule.")
        
# --------------------------------------------------
# 🔹 Sanguine Sunday Signup System
# --------------------------------------------------

# --- Message Content ---
SANG_MESSAGE_IDENTIFIER = "Sanguine Sunday Sign Up"
SANG_MESSAGE = "\n".join([
    f"{SANG_MESSAGE_IDENTIFIER} - Hosted by Macflag",
    "Looking for a fun Sunday activity? Look no farther than Sanguine Sunday! Spend an afternoon/evening sending TOBs with clan members. The focus on this event is on Learners and general KC.",
    "",
    "We plan to have mentors on hand to help out with the learners. Learner is someone who need the mechanics explained for each room.",
    "",
    "LEARNERS - please review this thread, watch the xzact guides, and get your plugins setup before Sunday - <#1388887895837773895>",
    "",
    "No matter if you're a learner or an experienced raider, we STRONGLY ENCOURAGE you use one of the setups in this thread. We have setups for both learners and experienced (rancour meta setup) - <#1388884558191268070>",
    "",
    "If you want to participate, leave a reaction to the post depending on your skill level.",
    "",
    "⚪ - Learner",
    "🔵 - Proficient",
    "🔴 - Mentor",
    "",
    "https://discord.com/events/1272629330115297330/1386302870646816788",
    "",
    f"||<@&{MENTOR_ROLE_ID}> <@&{SANG_ROLE_ID}> <@&{TOB_ROLE_ID}> <@&{EVENTS_ROLE_ID}>||"
])


LEARNER_REMINDER_IDENTIFIER = "Sanguine Sunday Learner Reminder"
LEARNER_REMINDER_MESSAGE = "\n".join([
    f"### {LEARNER_REMINDER_IDENTIFIER} ⏰",
    "This is a reminder for all learners who signed up for Sanguine Sunday!",
    "",
    "Please make sure you have reviewed the following guides and have your gear and plugins ready to go:",
    "- **Setups:** <#1388884558191268070>",
    "- **Guides & Plugins:** <#1388887895837773895>",
    "",
    "We look forward to seeing you there!"
])

SIGNUP_REACTIONS = ["⚪", "🔵", "🔴"]

# --- Helper Function ---
async def find_latest_signup_message(channel: discord.TextChannel) -> Optional[discord.Message]:
    """Finds the most recent Sanguine Sunday signup message in a channel."""
    async for message in channel.history(limit=100):
        if message.author == bot.user and SANG_MESSAGE_IDENTIFIER in message.content:
            return message
    return None

# --- Core Functions ---
async def post_signup(channel: discord.TextChannel):
    """Posts the main signup message and adds initial reactions."""
    msg = await channel.send(SANG_MESSAGE)
    for reaction in SIGNUP_REACTIONS:
        await msg.add_reaction(reaction)
    print(f"✅ Posted Sanguine Sunday signup in #{channel.name}")

async def post_reminder(channel: discord.TextChannel):
    """Finds learners and posts a reminder, cleaning up old ones."""
    signup_message = await find_latest_signup_message(channel)
    if not signup_message:
        print("⚠️ Could not find a signup message to post a reminder for.")
        return None  # Return None to indicate failure

    # Delete previous reminders from the bot
    async for message in channel.history(limit=50):
        if message.author == bot.user and LEARNER_REMINDER_IDENTIFIER in message.content:
            await message.delete()

    learners = []
    # Ensure we get the latest reaction data
    fresh_message = await channel.fetch_message(signup_message.id)
    for reaction in fresh_message.reactions:
        if str(reaction.emoji) == "⚪":
            async for user in reaction.users():
                if not user.bot:
                    learners.append(user.mention)
            break

    if not learners:
        reminder_content = f"{LEARNER_REMINDER_MESSAGE}\n\n_No learners have signed up yet._"
    else:
        learner_pings = " ".join(learners)
        reminder_content = f"{LEARNER_REMINDER_MESSAGE}\n\n**Learners:** {learner_pings}"

    await channel.send(reminder_content, allowed_mentions=discord.AllowedMentions(users=True))
    print(f"✅ Posted Sanguine Sunday learner reminder in #{channel.name}")
    return True  # Return True for success


# --- Slash Command ---
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
            await interaction.followup.send("⚠️ Could not find the signup message to post a reminder for.")

@sangsignup.error
async def sangsignup_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingRole):
        await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
    else:
        print(f"Error in sangsignup command: {error}")
        await interaction.followup.send(f"An unexpected error occurred. Please check the logs.", ephemeral=True)


# --- Scheduled Tasks ---
@tasks.loop(time=time(hour=11, minute=0, tzinfo=CST))
async def scheduled_post_signup():
    """Posts the signup message every Friday at 11:00 AM CST."""
    if datetime.now(CST).weekday() == 4:  # 4 = Friday
        channel = bot.get_channel(SANG_CHANNEL_ID)
        if channel:
            await post_signup(channel)

@tasks.loop(time=time(hour=14, minute=0, tzinfo=CST))
async def scheduled_post_reminder():
    """Posts the learner reminder every Saturday at 2:00 PM CST."""
    if datetime.now(CST).weekday() == 5:  # 5 = Saturday
        channel = bot.get_channel(SANG_CHANNEL_ID)
        if channel:
            await post_reminder(channel)

@tasks.loop(minutes=2)
async def maintain_reactions():
    """Ensures the signup reactions are always visible on the latest signup message."""
    channel = bot.get_channel(SANG_CHANNEL_ID)
    if not channel:
        return

    signup_message = await find_latest_signup_message(channel)
    if not signup_message:
        return

    current_reactions = {str(r.emoji): r for r in signup_message.reactions}

    for emoji in SIGNUP_REACTIONS:
        reaction = current_reactions.get(emoji)

        # If the reaction is missing entirely, the bot should add it.
        if not reaction:
            try:
                await signup_message.add_reaction(emoji)
            except (discord.NotFound, discord.Forbidden):
                pass  # Message was deleted or permissions changed
            continue

        # If the reaction exists, check who has reacted.
        users = [user async for user in reaction.users()]
        bot_has_reacted = bot.user in users

        # Goal: Bot should react if and only if no other user has.
        if bot_has_reacted and len(users) > 1:
            # Bot has reacted, but so has someone else. Remove bot's reaction.
            try:
                await signup_message.remove_reaction(emoji, bot.user)
            except (discord.NotFound, discord.Forbidden):
                pass
        elif not bot_has_reacted and len(users) == 0:
            # No one has reacted, and the bot hasn't either. Add the bot's reaction.
             try:
                await signup_message.add_reaction(emoji)
             except (discord.NotFound, discord.Forbidden):
                pass


@scheduled_post_signup.before_loop
@scheduled_post_reminder.before_loop
@maintain_reactions.before_loop
@post_daily_schedule.before_loop
async def before_scheduled_tasks():
    await bot.wait_until_ready()

# ---------------------------
# 🔹 Bot Events
# ---------------------------

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # This is required to process other non-slash commands if you have any.
    # Since this bot seems to be slash-command only, this line might not be strictly
    # necessary unless you have other on_message logic.
    await bot.process_commands(message)

    parent_channel_id = None
    if isinstance(message.channel, discord.Thread):
        parent_channel_id = message.channel.parent.id
    elif isinstance(message.channel, discord.TextChannel):
        parent_channel_id = message.channel.id

    # ---------------------------
    # 📸 Collat handler
    # ---------------------------
    if message.channel.id == COLLAT_CHANNEL_ID:
        has_pasted_image = any(embed.image for embed in message.embeds)
        is_reply = message.reference is not None
        valid_mention = None
        if message.mentions and not is_reply:
            valid_mention = message.mentions[0]

        if valid_mention or message.attachments or has_pasted_image:
            view = CollatButtons(message.author, valid_mention)
            await message.reply("Collat actions:", view=view, allowed_mentions=discord.AllowedMentions.none())
        
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    
    # Start the RSN writer task
    asyncio.create_task(rsn_writer())
    
    # Start the Sanguine Sunday tasks
    if not scheduled_post_signup.is_running():
        scheduled_post_signup.start()
        print("✅ Started scheduled signup task.")
    if not scheduled_post_reminder.is_running():
        scheduled_post_reminder.start()
        print("✅ Started scheduled reminder task.")
    if not maintain_reactions.is_running():
        maintain_reactions.start()
        print("✅ Started reaction maintenance task.")

    # Start the event schedule task
    if not post_daily_schedule.is_running():
        post_daily_schedule.start()
        print("✅ Started daily event schedule task.")

    # Panel initializations
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
        
        boss_embed = discord.Embed(title="⚔︎ 𝔊𝔯𝔬𝔲p 𝔅𝔬𝔰𝔰𝔢𝔰 ⚔︎", description="", color=0x0000ff)
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


