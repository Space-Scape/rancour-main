import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import asyncio
import re
from discord import ui, ButtonStyle
from discord.ui import View, Button, Modal, TextInput
from typing import Optional, List, Dict, Any
from datetime import datetime, time as dt_time
from pathlib import Path
from zoneinfo import ZoneInfo

# ---------------------------
# 🔹 Constants
# ---------------------------
CST = ZoneInfo('America/Chicago')
GUILD_ID = 1272629330115297330

# Channel and Role IDs
SANG_CHANNEL_ID = 1338295765759688767
STAFF_ROLE_ID = 1272635396991221824
MEMBER_ROLE_ID = 1272633036814946324
MENTOR_ROLE_ID = 1306021911830073414
SANG_ROLE_ID = 1387153629072592916
TOB_ROLE_ID = 1272694636921753701
SANG_VC_CATEGORY_ID = 1376645103803830322
SANG_MATCHMAKING_VC_ID = 1461429914338332845
SANG_VC_LINK = "https://discord.com/channels/1272629330115297330/1461429914338332845"

SCRIPT_DIR = Path(__file__).parent.resolve()
SANG_MESSAGE_ID_FILE = SCRIPT_DIR / "sang_message_id.txt"
SANG_DAY_FILE = SCRIPT_DIR / "sang_day.txt"

# GSheet Config
SANG_SHEET_ID = "1CCpDAJO7Cq581yF_-rz3vx7L_BTettVaKglSvOmvTOE"
SANG_SHEET_TAB_NAME = "SangSignups"
SANG_HISTORY_TAB_NAME = "History"
SANG_SHEET_HEADER = [
    "Discord_ID", "Discord_Name", "Region", "KC", "Has_Scythe", 
    "Proficiency", "Learning Freeze", "Play With Learners", 
    "Timestamp", "Blacklist", "Whitelist"
]

# Store last generated teams in memory
last_generated_teams: List[List[Dict[str, Any]]] = []

# ---------------------------
# 🔹 Helper Functions
# ---------------------------

def get_sang_message(day: str) -> str:
    return f"""\
# Sanguine {day} Sign Up – Hosted by SpaceScape <:sanguine_saturday:1469004948594364528>

Looking for a fun {day} activity? Look no farther than **Sanguine {day}!**
Spend an afternoon or evening sending **Theatre of Blood** runs with clan members.
The focus on this event is on **Learners** and general KC.

We plan to have mentors on hand to help out with the learners.
A learner is someone who needs the mechanics explained for each room.

───────────────────────────────
**ToB Learner Resource Hub - made by Macflag**

All Theatre of Blood guides, setups, and related resources are organized here:
➤ [**ToB Resource Hub**](https://discord.com/channels/1272629330115297330/1426262876699496598)

───────────────────────────────

LEARNERS – please review this thread, watch the xzact guides, and get your plugins set up before {day}:
➤ [**Guides & Plugins**](https://discord.com/channels/1272629330115297330/1388887895837773895)

No matter if you're a learner or an experienced raider, we strongly encourage you to use one of the setups in the threads provided by Macflag:

⚪ [**Learner Setups**](https://discord.com/channels/1272629330115297330/1426263868950450257)
🔵 [**Rancour Meta Setups**](https://discord.com/channels/1272629330115297330/1426272592452391012)

───────────────────────────────
**Sign-Up Here!**

Click a button below to sign up for the event.
- **Raider:** Fill out the form with your KC and Region.
- **Mentor:** Fill out the form to sign up as a mentor.
- **Withdraw:** Remove your name from this week's signup list.

The form will remember your answers from past events! 
You only need to edit Kc's if they changed.

Event link: <https://discord.com/events/1272629330115297330/1469002724979904616>

||<@&{MENTOR_ROLE_ID}> <@&{SANG_ROLE_ID}> <@&{TOB_ROLE_ID}>||
"""

def get_learner_reminder(day: str) -> str:
    return f"""\
# Sanguine {day} Learner Reminder ⏰ <:sanguine_saturday:1469004948594364528>

This is a reminder for all learners who signed up for Sanguine {day}!

Please make sure you have reviewed the following guides and have your gear and plugins ready to go:
• **[ToB Resource Hub](https://discord.com/channels/1272629330115297330/1426262876699496598)**
• **[Learner Setups](https://discord.com/channels/1272629330115297330/1426263868950450257)**
• **[Rancour Meta Setups](https://discord.com/channels/1272629330115297330/1426272592452391012)**
• **[Guides & Plugins](https://discord.com/channels/1272629330115297330/1426263621440372768)**

We will be gathering in the **[Sanguine {day} VC]({SANG_VC_LINK})**!
We look forward to seeing you there!
"""

def sanitize_nickname(name: str) -> str:
    if not name: return ""
    name = re.sub(r'\s*\([^)]*#\d{4}\)', '', name)
    name = re.sub(r'\s*\[[^\]]*#\d{4}\]', '', name)
    name = re.sub(r'^[!#@]+', '', name)
    return name.strip()

def normalize_role(p: dict) -> str:
    prof = str(p.get("proficiency","")).strip().lower()
    if prof == "mentor": return "mentor"
    try: kc = int(p.get("kc") or p.get("KC") or 0)
    except Exception: return prof
    if kc <= 25: return "new"
    if 26 <= kc <= 49: return "learner"
    if 50 <= kc <= 100: return "proficient"
    return "highly proficient"

PROF_ORDER = {"mentor": 0, "highly proficient": 1, "proficient": 2, "learner": 3, "new": 4}

def prof_rank(p: dict) -> int:
    return PROF_ORDER.get(normalize_role(p), 99)

def scythe_icon(p: dict) -> str:
    return " • <:tob:1272864087105208364>" if p.get("has_scythe") else ""

def freeze_icon(p: dict) -> str:
    return " • ❄️" if p.get("learning_freeze") else ""

def is_blacklist_violation(player: Dict[str, Any], team: List[Dict[str, Any]]) -> bool:
    player_blacklist = player.get("blacklist", set())
    player_id_str = str(player.get("user_id"))
    for p_in_team in team:
        if str(p_in_team.get("user_id")) in player_blacklist: return True 
        if player_id_str in p_in_team.get("blacklist", set()): return True 
    return False

def check_merge_blacklist(clique_to_add: List[Dict], current_team: List[Dict]) -> bool:
    for new_p in clique_to_add:
        if is_blacklist_violation(new_p, current_team): return True
    return False

def get_valid_blocks(available_raiders: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """Groups players based on mutual whitelists. Dissolves if > 5 or internal blacklists found."""
    if not available_raiders: return []
    player_map = {str(p["user_id"]): p for p in available_raiders}
    adjacency = {uid: set() for uid in player_map}

    for p1 in available_raiders:
        id1 = str(p1["user_id"])
        for id2 in p1.get("whitelist", set()):
            if id2 in player_map and id2 != id1:
                adjacency[id1].add(id2)
                adjacency[id2].add(id1)

    visited = set()
    blocks = []

    for uid in player_map:
        if uid not in visited:
            component = []
            queue = [uid]
            visited.add(uid)
            while queue:
                curr = queue.pop(0)
                component.append(player_map[curr])
                for neighbor in adjacency[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            
            # Validate component
            valid = True
            if len(component) > 5:
                valid = False
            else:
                for p in component:
                    if is_blacklist_violation(p, [other for other in component if other != p]):
                        valid = False
                        break

            if valid:
                component.sort(key=prof_rank)
                blocks.append(component)
            else:
                # Break up invalid whitelists into individuals so they don't break matchmaking
                for p in component:
                    blocks.append([p])

    return blocks

def matchmaking_algorithm(available_raiders: List[Dict[str, Any]]):
    """
    Robust Constraint-Based Matchmaking:
    - Team size MUST be 3, 4, or 5.
    - Honors 'Play With Learners' preference.
    - Soft prioritizes Region matching.
    """
    if not available_raiders: return [], []
    print(f"\n🧩 Starting Matchmaking for {len(available_raiders)} players...")

    # Normalize preferences
    for p in available_raiders:
        p['play_with_learners'] = str(p.get("play_with_learners", "TRUE")).upper() in ["TRUE", "YES", "Y"]
        p['region'] = str(p.get("region", "Other")).upper()
        if p['region'] not in ["NA", "EU"]: p['region'] = "OTHER"
        if p['proficiency'] == 'mentor': p['play_with_learners'] = True # Mentors must play with learners

    blocks = get_valid_blocks(available_raiders)
    
    mentor_blocks = [b for b in blocks if any(p['proficiency'] == 'mentor' for p in b)]
    learner_blocks = [b for b in blocks if any(p['proficiency'] in ('learner', 'new') for p in b)]
    standard_blocks = [b for b in blocks if b not in mentor_blocks and b not in learner_blocks]

    teams = []
    stranded = []

    # 1. Initialize Mentor Teams
    for mb in mentor_blocks:
        teams.append({'members': mb, 'is_mentor': True})

    # 2. Assign Learners
    learner_blocks.sort(key=len, reverse=True)
    for lb in learner_blocks:
        best_team = None
        best_score = -9999
        for t in teams:
            if not t['is_mentor']: continue
            if len(t['members']) + len(lb) > 5: continue
            if check_merge_blacklist(lb, t['members']): continue

            score = 0
            team_regions = [p['region'] for p in t['members']]
            lb_regions = [p['region'] for p in lb]
            if any(r in team_regions for r in lb_regions): score += 10 # Match Region
            score -= len(t['members']) # Prefer smaller teams to spread load

            if score > best_score:
                best_score = score
                best_team = t

        if best_team:
            best_team['members'].extend(lb)
        else:
            stranded.extend(lb) # Cannot fit learner, strand them to avoid forcing them into a no-mentor run.

    # 3. Fill Mentor Teams with Support
    support_blocks = [b for b in standard_blocks if all(p['play_with_learners'] for p in b)]
    other_blocks = [b for b in standard_blocks if b not in support_blocks]

    for t in teams:
        if not t['is_mentor']: continue
        while len(t['members']) < 4: # Aim for at least 4 in mentor teams
            best_sb = None
            best_score = -9999
            for sb in support_blocks:
                if len(t['members']) + len(sb) > 5: continue
                if check_merge_blacklist(sb, t['members']): continue
                
                score = 0
                if any(p['region'] in [m['region'] for m in t['members']] for p in sb): score += 10
                if any(p['proficiency'] == 'highly proficient' for p in sb): score += 5
                
                if score > best_score:
                    best_score = score
                    best_sb = sb
                    
            if best_sb:
                t['members'].extend(best_sb)
                support_blocks.remove(best_sb)
            else:
                break

    standard_blocks = support_blocks + other_blocks

    # 4. Create Standard Teams
    standard_teams = []
    standard_blocks.sort(key=lambda b: (len(b), any(p['proficiency'] == 'highly proficient' for p in b)), reverse=True)

    for b in standard_blocks:
        placed = False
        # Try to place in an existing standard team
        for st in standard_teams:
            if len(st['members']) + len(b) <= 5:
                if not check_merge_blacklist(b, st['members']):
                    # Check Region soft preference (but pack tightly anyway)
                    st['members'].extend(b)
                    placed = True
                    break
        if not placed:
            standard_teams.append({'members': b, 'is_mentor': False})

    teams.extend(standard_teams)

    # 5. Fix Team Sizes (Min 3, Max 5)
    changed = True
    while changed:
        changed = False
        small_teams = sorted([t for t in teams if len(t['members']) < 3], key=lambda t: len(t['members']))
        if not small_teams: break

        target_team = small_teams[0]
        stolen = False
        large_teams = sorted([t for t in teams if len(t['members']) > 3], key=lambda t: len(t['members']), reverse=True)

        for lt in large_teams:
            for p in list(lt['members']):
                # Strict Rules for moving players:
                if lt['is_mentor']:
                    mentors_in_lt = [m for m in lt['members'] if m['proficiency'] == 'mentor']
                    if p['proficiency'] == 'mentor' and len(mentors_in_lt) <= 1: continue # Don't steal the only mentor
                    if p['proficiency'] in ['learner', 'new']: continue # Don't pull learners away from mentors

                if target_team['is_mentor'] and not p['play_with_learners']: continue
                if not target_team['is_mentor'] and p['proficiency'] in ['learner', 'new', 'mentor']: continue

                if not check_merge_blacklist([p], target_team['members']):
                    lt['members'].remove(p)
                    target_team['members'].append(p)
                    stolen = True
                    changed = True
                    break
            if stolen: break

        if not stolen:
            teams.remove(target_team)
            stranded.extend(target_team['members'])
            changed = True

    final_teams = [t['members'] for t in teams if 3 <= len(t['members']) <= 5]
    print(f"✅ Result: {len(final_teams)} Valid Teams (Sizes 3-5), {len(stranded)} Stranded.")
    return final_teams, stranded

def format_player_line_plain(guild: discord.Guild, p: dict) -> str:
    nickname = p.get("user_name") or "Unknown"
    role_text = p.get("proficiency", "Unknown").replace(" ", "-").capitalize().replace("-", " ")
    kc_raw = p.get("kc", 0)
    kc_text = f"({kc_raw} KC)" if isinstance(kc_raw, int) and kc_raw > 0 and role_text != "Mentor" and kc_raw != 9999 else ""
    scythe = scythe_icon(p)
    freeze = freeze_icon(p)
    region = f"[{p.get('region', 'OTHER')}]"
    no_l = " 🚫(No-Learners)" if role_text not in ["Mentor", "Learner", "New"] and not p.get("play_with_learners", True) else ""
    return f"{nickname} {region} • **{role_text}** {kc_text}{scythe}{freeze}{no_l}"

def format_player_line_mention(guild: discord.Guild, p: dict) -> str:
    try:
        uid = int(p["user_id"])
        member = guild.get_member(uid)
        mention = member.mention if member else f"<@{uid}>"
    except Exception:
        mention = f"@{p.get('user_name', 'Unknown')}"
        
    role_text = p.get("proficiency", "Unknown").replace(" ", "-").capitalize().replace("-", " ")
    kc_raw = p.get("kc", 0)
    kc_text = f"({kc_raw} KC)" if isinstance(kc_raw, int) and kc_raw > 0 and role_text != "Mentor" and kc_raw != 9999 else ""
    scythe = scythe_icon(p)
    freeze = freeze_icon(p)
    region = f"[{p.get('region', 'OTHER')}]"
    no_l = " 🚫(No-Learners)" if role_text not in ["Mentor", "Learner", "New"] and not p.get("play_with_learners", True) else ""
    return f"{mention} {region} • **{role_text}** {kc_text}{scythe}{freeze}{no_l}"

# ---------------------------
# 🔹 UI Modals & Views
# ---------------------------

class UserSignupForm(Modal, title="Sanguine Saturday Signup"):
    region = TextInput(label="Region (NA, EU, Other)", placeholder="NA, EU, or Other", style=discord.TextStyle.short, max_length=5, required=True)
    kc = TextInput(label="Normal Mode ToB KC?", placeholder="0-10=New, 11-25=Learner, 26-100=Proficient", style=discord.TextStyle.short, max_length=5, required=True)
    has_scythe = TextInput(label="Do you have a Scythe? (Yes/No)", placeholder="Yes or No ONLY", style=discord.TextStyle.short, max_length=3, required=True)
    learning_freeze = TextInput(label="Learn freeze role? (Yes or leave blank)", placeholder="Yes or blank", style=discord.TextStyle.short, max_length=3, required=False)

    def __init__(self, cog: 'SanguineCog', previous_data: dict = None):
        day = cog.get_event_day()
        super().__init__(title=f"Sanguine {day} Signup")
        self.cog = cog
        self.previous_data = previous_data 
        if previous_data:
            self.region.default = previous_data.get("Region", "")
            kc_val = previous_data.get("KC", "")
            self.kc.default = str(kc_val) if kc_val not in ["", None, "X"] else ""
            self.has_scythe.default = "Yes" if previous_data.get("Has_Scythe", False) else "No"
            self.learning_freeze.default = "Yes" if previous_data.get("Learning Freeze", False) else ""
        
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        if not self.cog.sang_sheet:
            await interaction.followup.send("⚠️ Error: The signup sheet is not connected. Please contact staff.", ephemeral=True)
            return
        
        try:
            kc_value = int(str(self.kc))
            if kc_value < 0: raise ValueError("KC cannot be negative.")
        except ValueError:
            await interaction.followup.send("⚠️ Error: Kill Count must be a valid number.", ephemeral=True)
            return
        
        scythe_value = str(self.has_scythe).strip().lower()
        if scythe_value not in ["yes", "no", "y", "n"]:
            await interaction.followup.send("⚠️ Error: Scythe must be 'Yes' or 'No'.", ephemeral=True)
            return
        has_scythe_bool = scythe_value in ["yes", "y"]

        # Inherit backend tag for learner teams, default to True
        play_learners_bool = self.previous_data.get("Play With Learners", True) if self.previous_data else True

        proficiency_value = ""
        if kc_value <= 10: proficiency_value = "New"
        elif 11 <= kc_value <= 49: proficiency_value = "Learner"
        elif 50 <= kc_value <= 100: proficiency_value = "Proficient"
        else: proficiency_value = "Highly Proficient"

        region_value = str(self.region).strip().upper()
        if region_value not in ["NA", "EU"]: region_value = "OTHER"
        
        learning_freeze_value = str(self.learning_freeze).strip().lower()
        learning_freeze_bool = learning_freeze_value in ["yes", "y"]

        user_id = str(interaction.user.id)
        user_name = sanitize_nickname(interaction.user.display_name)
        timestamp = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S")
        
        blacklist_value = self.previous_data.get("Blacklist", "") if self.previous_data else ""
        whitelist_value = self.previous_data.get("Whitelist", "") if self.previous_data else ""

        row_data = [user_id, user_name, region_value, kc_value, has_scythe_bool, proficiency_value, learning_freeze_bool, play_learners_bool, timestamp, blacklist_value, whitelist_value]
        
        try:
            sang_sheet_success, history_sheet_success = await self.cog._write_to_sheets_in_thread(user_id, row_data)
            if sang_sheet_success and history_sheet_success:
                await interaction.followup.send(
                    f"✅ **You are signed up as {proficiency_value}!**\n"
                    f"**KC:** {kc_value}\n"
                    f"**Region:** {region_value}\n"
                    f"**Scythe:** {'Yes' if has_scythe_bool else 'No'}\n"
                    f"**Learn Freeze:** {'Yes' if learning_freeze_bool else 'No'}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send("⚠️ An error occurred while saving your signup. Please contact staff.", ephemeral=True)
        except Exception as e:
            print(f"🔥🔥🔥 UNCAUGHT ERROR IN UserSignupForm on_submit: {e}")
            await interaction.followup.send("⚠️ A critical error occurred. Please tell staff to check the bot console.", ephemeral=True)


class MentorSignupForm(Modal, title="Sanguine Saturday Mentor Signup"):
    region = TextInput(label="Region (NA, EU, Other)", placeholder="NA, EU, or Other", style=discord.TextStyle.short, max_length=5, required=True)
    kc = TextInput(label="Normal Mode ToB KC?", placeholder="150+", style=discord.TextStyle.short, max_length=5, required=True)
    has_scythe = TextInput(label="Do you have a Scythe? (Yes/No)", placeholder="Yes or No", style=discord.TextStyle.short, max_length=3, required=True)

    def __init__(self, cog: 'SanguineCog', previous_data: dict = None):
        super().__init__(title="Sanguine Saturday Mentor Signup")
        self.cog = cog
        self.previous_data = previous_data
        if previous_data:
            self.region.default = previous_data.get("Region", "")
            kc_val = previous_data.get("KC", "")
            self.kc.default = str(kc_val) if kc_val not in ["", None, "X"] else ""
            self.has_scythe.default = "Yes" if previous_data.get("Has_Scythe", False) else "No"
        
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        if not self.cog.sang_sheet:
            await interaction.followup.send("⚠️ Error: The signup sheet is not connected.", ephemeral=True)
            return
        
        try:
            kc_value = int(str(self.kc))
            if kc_value < 50:
                await interaction.followup.send("⚠️ Mentors should have 50+ KC to sign up via form.", ephemeral=True)
                return
        except ValueError:
            await interaction.followup.send("⚠️ Error: Kill Count must be a valid number.", ephemeral=True)
            return
        
        scythe_value = str(self.has_scythe).strip().lower()
        if scythe_value not in ["yes", "no", "y", "n"]:
            await interaction.followup.send("⚠️ Error: Scythe must be 'Yes' or 'No'.", ephemeral=True)
            return
        has_scythe_bool = scythe_value in ["yes", "y"]

        region_value = str(self.region).strip().upper()
        if region_value not in ["NA", "EU"]: region_value = "OTHER"

        proficiency_value = "Mentor"
        user_id = str(interaction.user.id)
        user_name = sanitize_nickname(interaction.user.display_name)
        timestamp = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S")
        
        blacklist_value = self.previous_data.get("Blacklist", "") if self.previous_data else ""
        whitelist_value = self.previous_data.get("Whitelist", "") if self.previous_data else ""

        # Mentors inherently play with learners (True)
        row_data = [user_id, user_name, region_value, kc_value, has_scythe_bool, proficiency_value, False, True, timestamp, blacklist_value, whitelist_value]

        try:
            sang_sheet_success, history_sheet_success = await self.cog._write_to_sheets_in_thread(user_id, row_data)
            if sang_sheet_success and history_sheet_success:
                await interaction.followup.send(
                    f"✅ **You are signed up as a Mentor!**\n"
                    f"**KC:** {kc_value}\n"
                    f"**Region:** {region_value}\n"
                    f"**Scythe:** {'Yes' if has_scythe_bool else 'No'}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send("⚠️ An error occurred while saving your signup. Please contact staff.", ephemeral=True)
        except Exception as e:
            print(f"🔥🔥🔥 UNCAUGHT ERROR IN MentorSignupForm on_submit: {e}")
            await interaction.followup.send("⚠️ A critical error occurred. Please tell staff to check the bot console.", ephemeral=True)


class WithdrawalButton(ui.Button):
    def __init__(self, cog: 'SanguineCog'):
        super().__init__(label="Withdraw", style=ButtonStyle.secondary, custom_id="sang_withdraw", emoji="❌")
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        user_id = str(interaction.user.id)
        user_name = interaction.user.display_name

        if not self.cog.sang_sheet:
            await interaction.followup.send("⚠️ Error: The Sanguine Signup sheet is not connected.", ephemeral=True)
            return

        try:
            deleted = await self.cog._withdraw_user_in_thread(user_id)
            if deleted:
                await interaction.followup.send(f"✅ **{user_name}**, you have been successfully withdrawn from this week's Sanguine Saturday signups.", ephemeral=True)
            else:
                await interaction.followup.send(f"ℹ️ {user_name}, you are not currently signed up for this week's event.", ephemeral=True)
        except Exception as e:
            print(f"🔥 GSpread error on withdrawal: {e}")
            await interaction.followup.send("⚠️ An error occurred while processing your withdrawal.", ephemeral=True)

class SignupView(View):
    def __init__(self, cog: 'SanguineCog'):
        super().__init__(timeout=None)
        self.cog = cog
        self.add_item(WithdrawalButton(self.cog))

    @ui.button(label="Sign Up as Raider", style=ButtonStyle.success, custom_id="sang_signup_raider", emoji="📝")
    async def user_signup_button(self, interaction: discord.Interaction, button: Button):
        previous_data = self.cog.get_previous_signup(str(interaction.user.id))
        await interaction.response.send_modal(UserSignupForm(self.cog, previous_data=previous_data))

    @ui.button(label="Sign Up as Mentor", style=ButtonStyle.danger, custom_id="sang_signup_mentor", emoji="🎓")
    async def mentor_signup_button(self, interaction: discord.Interaction, button: Button):
        user = interaction.user
        member = interaction.guild.get_member(user.id)
        if not member:
            await interaction.response.send_message("⚠️ Could not verify your roles. Please try again.", ephemeral=True)
            return
        previous_data = self.cog.get_previous_signup(str(user.id))
        if previous_data and previous_data.get("KC") == "X":
            previous_data["KC"] = "" 
        await interaction.response.send_modal(MentorSignupForm(self.cog, previous_data=previous_data))


# ---------------------------
# 🔹 Sanguine Cog Class
# ---------------------------

class SanguineCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sang_sheet = None
        self.history_sheet = None
        self.live_signup_message_id = None
        self.live_signup_message_lock = asyncio.Lock()
        
        # Initialize Google Sheets
        try:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
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
            
            sang_google_sheet = sheet_client.open_by_key(SANG_SHEET_ID)
            
            # Safe header migration
            try:
                self.sang_sheet = sang_google_sheet.worksheet(SANG_SHEET_TAB_NAME)
                header = self.sang_sheet.row_values(1)
                if header != SANG_SHEET_HEADER:
                    print("⚠️ Sanguine sheet header mismatch. Updating headers safely...")
                    self.sang_sheet.update(values=[SANG_SHEET_HEADER], range_name='A1:K1')
            except gspread.exceptions.WorksheetNotFound:
                print(f"'{SANG_SHEET_TAB_NAME}' not found. Creating...")
                self.sang_sheet = sang_google_sheet.add_worksheet(title=SANG_SHEET_TAB_NAME, rows="100", cols="20")
                self.sang_sheet.append_row(SANG_SHEET_HEADER)
            
            try:
                self.history_sheet = sang_google_sheet.worksheet(SANG_HISTORY_TAB_NAME)
                header = self.history_sheet.row_values(1)
                if header != SANG_SHEET_HEADER:
                    print("⚠️ Sanguine history sheet header mismatch. Updating headers safely...")
                    self.history_sheet.update(values=[SANG_SHEET_HEADER], range_name='A1:K1')
            except gspread.exceptions.WorksheetNotFound:
                print(f"'{SANG_HISTORY_TAB_NAME}' not found. Creating...")
                self.history_sheet = sang_google_sheet.add_worksheet(title=SANG_HISTORY_TAB_NAME, rows="1000", cols="20")
                self.history_sheet.append_row(SANG_SHEET_HEADER)
            
            print("✅ Sanguine Cog: Google Sheets initialized successfully.")
        except Exception as e:
            print(f"🔥 CRITICAL ERROR initializing SanguineCog GSheets: {e}")

        self.bot.add_view(SignupView(self))

    def get_event_day(self) -> str:
        if SANG_DAY_FILE.exists(): return SANG_DAY_FILE.read_text().strip()
        return "Saturday"

    def set_event_day(self, day: str):
        SANG_DAY_FILE.write_text(day)
    
    @commands.Cog.listener()
    async def on_ready(self):
        await self.load_live_message_id()
        if not self.scheduled_post_signup.is_running(): self.scheduled_post_signup.start()
        if not self.scheduled_post_reminder.is_running(): self.scheduled_post_reminder.start()
        if not self.scheduled_clear_sang_sheet.is_running(): self.scheduled_clear_sang_sheet.start()
        print("Sanguine Cog is ready.")

    async def _write_to_sheets_in_thread(self, user_id: str, row_data: List[Any]) -> (bool, bool):
        def _blocking_sheet_write():
            sang_success, hist_success = False, False
            try:
                cell = self.sang_sheet.find(user_id, in_column=1)
                if cell is None: self.sang_sheet.append_row(row_data)
                else: self.sang_sheet.update(values=[row_data], range_name=f'A{cell.row}:K{cell.row}')
                sang_success = True
            except Exception as e: print(f"🔥 GSpread error on SangSignups: {e}")

            if self.history_sheet:
                try:
                    history_cell = self.history_sheet.find(user_id, in_column=1)
                    if history_cell is None: self.history_sheet.append_row(row_data)
                    else: self.history_sheet.update(values=[row_data], range_name=f'A{history_cell.row}:K{history_cell.row}')
                    hist_success = True
                except Exception as e: print(f"🔥 GSpread error on History: {e}")
            else: hist_success = True 
            
            return sang_success, hist_success
        
        loop = asyncio.get_running_loop()
        sang_sheet_success, history_sheet_success = await loop.run_in_executor(None, _blocking_sheet_write)
        if sang_sheet_success: await self.update_live_signup_message()
        return sang_sheet_success, history_sheet_success

    @app_commands.command(name="sangsetday", description="Set the event day to Saturday or Sunday.")
    @app_commands.checks.has_role(STAFF_ROLE_ID)
    @app_commands.choices(day=[
        app_commands.Choice(name="Saturday", value="Saturday"),
        app_commands.Choice(name="Sunday", value="Sunday")
    ])
    async def sangsetday(self, interaction: discord.Interaction, day: str):
        await interaction.response.defer(ephemeral=True, thinking=True)
        self.set_event_day(day)
        
        # Rename the designated channels
        text_channel = self.bot.get_channel(SANG_CHANNEL_ID)
        vc_channel = self.bot.get_channel(SANG_MATCHMAKING_VC_ID)
        
        text_name = f"🩸⎮sanguine-{day.lower()}"
        vc_name = f"Sang {day} Matchmaking"
        
        rename_status = ""
        try:
            if text_channel:
                await text_channel.edit(name=text_name)
            if vc_channel:
                await vc_channel.edit(name=vc_name)
            rename_status = " Channels have been renamed successfully."
        except discord.Forbidden:
            rename_status = "\n⚠️ *Could not rename channels (Bot is missing 'Manage Channels' permission).* "
        except discord.HTTPException as e:
            rename_status = f"\n⚠️ *Could not rename channels (Rate limited or HTTP error).* "
        
        await interaction.followup.send(f"✅ Sanguine event day set to **{day}**! Future signups and reminders will automatically adjust.{rename_status}", ephemeral=True)
        await self.update_live_signup_message()
    
    async def _withdraw_user_in_thread(self, user_id: str) -> bool:
        def _blocking_sheet_delete():
            try:
                cell = self.sang_sheet.find(user_id, in_column=1)
                if cell is None: return False
                self.sang_sheet.delete_rows(cell.row)
                return True
            except Exception as e:
                print(f"🔥 GSpread error on withdrawal (in thread): {e}")
                raise e 
        
        loop = asyncio.get_running_loop()
        deleted = await loop.run_in_executor(None, _blocking_sheet_delete)
        if deleted: await self.update_live_signup_message()
        return deleted

    async def _create_team_embeds(self, teams, title, description, color, guild, format_func):
        embeds = []
        if not teams: return embeds
        
        current_embed = discord.Embed(title=title, description=description, color=color)
        embeds.append(current_embed)
        field_count = 0
        FIELDS_PER_EMBED = 10
        
        for i, team in enumerate(teams, start=1):
            if field_count >= FIELDS_PER_EMBED:
                current_embed = discord.Embed(title=f"{title} (Page {len(embeds) + 1})", color=color)
                embeds.append(current_embed)
                field_count = 0
                
            team_sorted = sorted(team, key=prof_rank)
            lines = [format_func(guild, p) for p in team_sorted]
            
            current_embed.add_field(name=f"Team {i} (Size: {len(team)})", value="\n".join(lines) if lines else "—", inline=False)
            field_count += 1
            
        return embeds

    async def _generate_signups_embed(self) -> discord.Embed:
        day = self.get_event_day()
        embed = discord.Embed(
            title=f"<:sanguine_saturday:1469004948594364528> Sanguine {day} Signups",
            color=discord.Color.red(),
            timestamp=datetime.now(CST)
        )

        if not self.sang_sheet:
            embed.description = "⚠️ Bot could not connect to the signup sheet."
            return embed
        
        try:
            all_signups_records = self.sang_sheet.get_all_records()
            if not all_signups_records:
                embed.description = "No signups yet. Be the first!"
                embed.set_footer(text="Total Signups: 0")
                return embed
        except Exception as e:
            embed.description = "⚠️ An error occurred while fetching signups."
            return embed
        
        players = []
        for signup in all_signups_records:
            kc_raw = signup.get("KC", 0)
            try: kc_val = int(kc_raw)
            except (ValueError, TypeError): kc_val = 9999 if signup.get("Proficiency", "").lower() == 'mentor' else 0
            
            proficiency_val = signup.get("Proficiency", "").lower()
            if proficiency_val != 'mentor':
                if kc_val <= 10: proficiency_val = "new"
                elif 11 <= kc_val <= 49: proficiency_val = "learner"
                elif 50 <= kc_val <= 100: proficiency_val = "proficient"
                else: proficiency_val = "highly proficient"

            user_id = str(signup.get("Discord_ID"))
            whitelist_str = str(signup.get("Whitelist", "")).strip()
            whitelist_ids = set(id.strip() for id in whitelist_str.split(',') if id.strip()) if whitelist_str and whitelist_str != "None" else set()

            p_data = {
                "user_id": user_id,
                "user_name": sanitize_nickname(signup.get("Discord_Name")),
                "proficiency": proficiency_val,
                "kc": kc_val, 
                "has_scythe": str(signup.get("Has_Scythe", "FALSE")).upper() == "TRUE",
                "learning_freeze": str(signup.get("Learning Freeze", "FALSE")).upper() == "TRUE",
                "whitelist": whitelist_ids,
                "region": str(signup.get("Region", "OTHER")).upper()
            }
            players.append(p_data)
        
        try:
            # We approximate deficit logic using naive learner counts vs mentor counts since cliques are flexible now
            learner_count = sum(1 for p in players if p["proficiency"] in ["new", "learner"])
            mentor_count = sum(1 for p in players if p["proficiency"] == "mentor")
            deficit = (learner_count // 3 + (1 if learner_count % 3 else 0)) - mentor_count
            if deficit > 0:
                 embed.description = f"**⚠️ Mentors Needed:** We need roughly **{deficit}** more Mentor(s) to cover all learners!"
            else:
                 embed.description = "✅ Current signups have sufficient Mentor coverage."
        except Exception as e:
            print(f"Error calculating mentor deficit: {e}")

        players.sort(key=prof_rank)
        grouped_players = {}
        for p in players:
            prof = p['proficiency'].capitalize()
            if prof not in grouped_players: grouped_players[prof] = []
            grouped_players[prof].append(p)
            
        for prof_key in PROF_ORDER.keys():
            prof_name = prof_key.capitalize()
            if prof_name in grouped_players:
                player_list = grouped_players[prof_name]
                field_value = []
                for p in player_list:
                    scythe = scythe_icon(p)
                    freeze = freeze_icon(p)
                    region = f"[{p['region']}]"
                    field_value.append(f"{p['user_name']} {region}{scythe}{freeze}")
                
                embed.add_field(name=f"**{prof_name}** ({len(player_list)})", value="\n".join(field_value), inline=False)
                
        embed.set_footer(text=f"Total Signups: {len(players)}")
        return embed

    async def load_live_message_id(self):
        try:
            if SANG_MESSAGE_ID_FILE.exists():
                content = SANG_MESSAGE_ID_FILE.read_text().strip()
                if content:
                    self.live_signup_message_id = int(content)
                else: self.live_signup_message_id = None
            else: self.live_signup_message_id = None
        except Exception as e:
            self.live_signup_message_id = None

    async def save_live_message_id(self, message_id: Optional[int]):
        self.live_signup_message_id = message_id
        try:
            if message_id is None: SANG_MESSAGE_ID_FILE.unlink(missing_ok=True)
            else: SANG_MESSAGE_ID_FILE.write_text(str(message_id))
        except Exception as e: print(f"🔥 Failed to save live signup message ID: {e}")

    async def update_live_signup_message(self):
        async with self.live_signup_message_lock:
            if not self.live_signup_message_id: return
            new_embed = await self._generate_signups_embed()
            try:
                channel = self.bot.get_channel(SANG_CHANNEL_ID)
                if not channel: return
                message = await channel.fetch_message(self.live_signup_message_id)
                await message.edit(embed=new_embed)
            except discord.NotFound:
                await self.save_live_message_id(None)
            except Exception as e: print(f"🔥 Failed to update live signup message: {e}")

    def get_previous_signup(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.history_sheet: return None
        try:
            all_records = self.history_sheet.get_all_records()
            if not all_records: return None
            for record in reversed(all_records):
                if str(record.get("Discord_ID", "")) == user_id:
                    record["Has_Scythe"] = str(record.get("Has_Scythe", "FALSE")).upper() == "TRUE"
                    record["Learning Freeze"] = str(record.get("Learning Freeze", "FALSE")).upper() == "TRUE"
                    record["Play With Learners"] = str(record.get("Play With Learners", "TRUE")).upper() == "TRUE"
                    return record
            return None
        except Exception as e: return None

    async def post_signup(self, channel: discord.TextChannel):
        day = self.get_event_day()
        signup_message = await channel.send(get_sang_message(day), view=SignupView(self))
        try: await signup_message.pin()
        except Exception: pass

        try:
            initial_embed = await self._generate_signups_embed()
            live_message = await channel.send(embed=initial_embed)
            await self.save_live_message_id(live_message.id)
        except Exception as e: print(f"🔥 Failed to post live signup message: {e}")

    async def post_reminder(self, channel: discord.TextChannel):
        if not self.sang_sheet: return False
        day = self.get_event_day()
        try:
            async for message in channel.history(limit=50):
                if message.author == self.bot.user and "Learner Reminder" in message.content and "Sanguine" in message.content:
                    await message.delete()
        except Exception: pass

        learners = []
        try:
            all_signups = self.sang_sheet.get_all_records()
            for signup in all_signups:
                if str(signup.get("Proficiency", "")).lower() in ["learner", "new"]:
                    user_id = signup.get('Discord_ID')
                    if user_id: learners.append(f"<@{user_id}>")
            
            if not learners: reminder_content = f"{get_learner_reminder(day)}\n\n_No learners have signed up yet._"
            else: reminder_content = f"{get_learner_reminder(day)}\n\n**Learners:** {' '.join(learners)}"

            await channel.send(reminder_content, allowed_mentions=discord.AllowedMentions(users=True))
            await self.update_live_signup_message()
            return True
        except Exception as e: return False

    # --- Slash Commands ---
    
    @app_commands.command(name="sangsignup", description="Manage Sanguine Saturday signups.")
    @app_commands.checks.has_role(STAFF_ROLE_ID)
    @app_commands.describe(variant="Choose the action to perform.", channel="Optional channel.")
    @app_commands.choices(variant=[
        app_commands.Choice(name="Post Signup Message", value=1),
        app_commands.Choice(name="Post Learner Reminder", value=2),
    ])
    async def sangsignup(self, interaction: discord.Interaction, variant: int, channel: Optional[discord.TextChannel] = None):
        target_channel = channel or self.bot.get_channel(SANG_CHANNEL_ID)
        if not target_channel:
            await interaction.response.send_message("⚠️ Could not find the target channel.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        if variant == 1:
            await self.post_signup(target_channel)
            await interaction.followup.send(f"✅ Signup message & live embed posted in {target_channel.mention}.")
        elif variant == 2:
            result = await self.post_reminder(target_channel)
            if result: await interaction.followup.send(f"✅ Learner reminder posted in {target_channel.mention}.")
            else: await interaction.followup.send("⚠️ Could not post the reminder.")

    @app_commands.command(name="sangmatch", description="Create ToB teams from users in the designated voice channel.")
    @app_commands.checks.has_role(STAFF_ROLE_ID)
    async def sangmatch(self, interaction: discord.Interaction):
        prefix = "SanSat" if self.get_event_day() == "Saturday" else "SanSun"
        
        if not self.sang_sheet:
            await interaction.response.send_message("⚠️ Error: The Sanguine Saturday sheet is not connected.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=False)
        
        voice_channel = self.bot.get_channel(SANG_MATCHMAKING_VC_ID)
        if not voice_channel or not isinstance(voice_channel, discord.VoiceChannel):
            await interaction.followup.send("⚠️ Matchmaking voice channel not found or is not a voice channel.")
            return

        channel_name = voice_channel.name
        if not voice_channel.members:
            await interaction.followup.send(f"⚠️ No users are in {voice_channel.mention}.")
            return
        vc_member_ids = {str(member.id) for member in voice_channel.members if not member.bot}
        if not vc_member_ids:
            await interaction.followup.send(f"⚠️ No human users are in {voice_channel.mention}.")
            return
        
        try:
            all_signups_records = self.sang_sheet.get_all_records()
            if not all_signups_records:
                await interaction.followup.send("⚠️ There are no signups in the database.")
                return
        except Exception as e:
            await interaction.followup.send("⚠️ An error occurred fetching signups from the database.")
            return

        available_raiders = []
        for signup in all_signups_records:
            user_id = str(signup.get("Discord_ID"))
            if vc_member_ids and user_id not in vc_member_ids: continue
            
            kc_raw = signup.get("KC", 0)
            try: kc_val = int(kc_raw)
            except (ValueError, TypeError): kc_val = 9999 if signup.get("Proficiency", "").lower() == 'mentor' else 0
            
            proficiency_val = signup.get("Proficiency", "").lower()
            if proficiency_val != 'mentor':
                if kc_val <= 10: proficiency_val = "new"
                elif 11 <= kc_val <= 49: proficiency_val = "learner"
                elif 50 <= kc_val <= 100: proficiency_val = "proficient"
                else: proficiency_val = "highly proficient"

            blacklist_str = str(signup.get("Blacklist", "")).strip()
            blacklist_ids = set(id.strip() for id in blacklist_str.split(',') if id.strip()) if blacklist_str and blacklist_str != "None" else set()

            whitelist_str = str(signup.get("Whitelist", "")).strip()
            whitelist_ids = set(id.strip() for id in whitelist_str.split(',') if id.strip()) if whitelist_str and whitelist_str != "None" else set()

            available_raiders.append({
                "user_id": user_id,
                "user_name": sanitize_nickname(signup.get("Discord_Name")),
                "proficiency": proficiency_val,
                "kc": kc_val,
                "region": str(signup.get("Region", "OTHER")).upper(),
                "has_scythe": str(signup.get("Has_Scythe", "FALSE")).upper() == "TRUE",
                "learning_freeze": str(signup.get("Learning Freeze", "FALSE")).upper() == "TRUE",
                "play_with_learners": str(signup.get("Play With Learners", "TRUE")).upper() == "TRUE",
                "blacklist": blacklist_ids,
                "whitelist": whitelist_ids
            })

        if not available_raiders:
            await interaction.followup.send(f"⚠️ None of the users in {voice_channel.mention} have signed up for the event.")
            return

        teams, stranded_players = matchmaking_algorithm(available_raiders)

        guild = interaction.guild
        category = guild.get_channel(SANG_VC_CATEGORY_ID)
        
        if category and isinstance(category, discord.CategoryChannel):
            member_role = guild.get_role(MEMBER_ROLE_ID)
            overwrites = {}
            if member_role: overwrites[member_role] = discord.PermissionOverwrite(view_channel=True, connect=True, speak=True)

            for i, team in enumerate(teams):
                try:
                    mentor_name = sanitize_nickname(team[0].get("user_name", f"Team{i+1}")) if team else f"Team{i+1}"
                    new_vc = await category.create_voice_channel(name=f"{prefix}{mentor_name}", overwrites=overwrites)
                except Exception as e: print(f"Error creating VC: {e}") 

        post_channel = interaction.channel
        embed_title = f"Sanguine Saturday Teams - {channel_name}"
        embed_desc = f"Created {len(teams)} valid team(s) from {len(available_raiders)} available signed-up users.\n*Note: Team sizes strictly bounded to 3-5 players.*"
        if stranded_players:
            embed_desc += f"\n\n⚠️ **Stranded Players:** {', '.join([p['user_name'] for p in stranded_players])}"
        
        team_embeds = await self._create_team_embeds(teams, embed_title, embed_desc, discord.Color.red(), guild, format_player_line_mention)
        
        global last_generated_teams
        last_generated_teams = teams

        for i, embed in enumerate(team_embeds):
            if i == 0: await interaction.followup.send(embed=embed)
            else: await post_channel.send(embed=embed)
        
    @app_commands.command(name="sangmatchtest", description="Create ToB teams without pinging or creating voice channels.")
    @app_commands.checks.has_role(STAFF_ROLE_ID)
    @app_commands.describe(voice_channel="Optional: The voice channel to pull users from. If omitted, uses all signups.")
    async def sangmatchtest(self, interaction: discord.Interaction, voice_channel: Optional[discord.VoiceChannel] = None):
        if not self.sang_sheet:
            await interaction.response.send_message("⚠️ Error: The Sanguine Saturday sheet is not connected.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=False)

        vc_member_ids = None
        channel_name = "All Signups"
        if voice_channel:
            channel_name = voice_channel.name
            if not voice_channel.members:
                await interaction.followup.send(f"⚠️ No users are in {voice_channel.mention}.")
                return
            vc_member_ids = {str(m.id) for m in voice_channel.members if not m.bot}
            if not vc_member_ids:
                await interaction.followup.send(f"⚠️ No human users are in {voice_channel.mention}.")
                return

        try: all_signups_records = self.sang_sheet.get_all_records()
        except Exception as e:
            await interaction.followup.send("⚠️ An error occurred fetching signups from the database.")
            return
        
        available_raiders = []
        for signup in all_signups_records:
            user_id = str(signup.get("Discord_ID"))
            if vc_member_ids and user_id not in vc_member_ids: continue
            
            kc_raw = signup.get("KC", 0)
            try: kc_val = int(kc_raw)
            except (ValueError, TypeError): kc_val = 9999 if signup.get("Proficiency", "").lower() == 'mentor' else 0
            
            proficiency_val = signup.get("Proficiency", "").lower()
            if proficiency_val != 'mentor':
                if kc_val <= 10: proficiency_val = "new"
                elif 11 <= kc_val <= 49: proficiency_val = "learner"
                elif 50 <= kc_val <= 100: proficiency_val = "proficient"
                else: proficiency_val = "highly proficient"

            blacklist_str = str(signup.get("Blacklist", "")).strip()
            blacklist_ids = set(id.strip() for id in blacklist_str.split(',') if id.strip()) if blacklist_str and blacklist_str != "None" else set()
            whitelist_str = str(signup.get("Whitelist", "")).strip()
            whitelist_ids = set(id.strip() for id in whitelist_str.split(',') if id.strip()) if whitelist_str and whitelist_str != "None" else set()

            available_raiders.append({
                "user_id": user_id, "user_name": sanitize_nickname(signup.get("Discord_Name")),
                "proficiency": proficiency_val, "kc": kc_val, "region": str(signup.get("Region", "OTHER")).upper(),
                "has_scythe": str(signup.get("Has_Scythe", "FALSE")).upper() == "TRUE",
                "learning_freeze": str(signup.get("Learning Freeze", "FALSE")).upper() == "TRUE",
                "play_with_learners": str(signup.get("Play With Learners", "TRUE")).upper() == "TRUE",
                "blacklist": blacklist_ids, "whitelist": whitelist_ids
            })

        if not available_raiders:
            await interaction.followup.send("⚠️ No eligible signups.")
            return

        teams, stranded_players = matchmaking_algorithm(available_raiders)

        embed_title = f"Sanguine Teams (Test, no pings/VC) - {channel_name}"
        embed_desc = f"Created {len(teams)} valid team(s) from {len(available_raiders)} available signed-up users."
        if stranded_players:
            embed_desc += f"\n\n⚠️ **Stranded Players:** {', '.join([p['user_name'] for p in stranded_players])}"

        team_embeds = await self._create_team_embeds(teams, embed_title, embed_desc, discord.Color.dark_gray(), interaction.guild, format_player_line_plain)

        global last_generated_teams
        last_generated_teams = teams
        
        for i, embed in enumerate(team_embeds):
            if i == 0: await interaction.followup.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
            else: await interaction.channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="sangexport", description="Export the most recently generated teams to a text file.")
    @app_commands.checks.has_any_role("Administrators", "Clan Staff", "Senior Staff", "Staff", "Trial Staff")
    async def sangexport(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        global last_generated_teams
        teams = last_generated_teams
        if not teams:
            await interaction.followup.send("⚠️ No teams found from this session.", ephemeral=True)
            return

        lines = []
        for i, team in enumerate(teams, start=1):
            lines.append(f"Team {i}")
            for p in team:
                sname = sanitize_nickname(p.get("user_name", "Unknown"))
                mid = p.get("user_id")
                id_text = str(mid) if mid is not None else "UnknownID"
                lines.append(f"  - {sname} — ID: {id_text}")
            lines.append("")
        txt = "\n".join(lines)

        export_dir = Path(os.getenv("SANG_EXPORT_DIR", "/mnt/data"))
        try: export_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            export_dir = Path("/tmp")
            export_dir.mkdir(parents=True, exist_ok=True)
        
        ts = datetime.now(CST).strftime("%Y%m%d_%H%M%S")
        outpath = export_dir / f"sanguine_teams_{ts}.txt"
        
        try:
            with open(outpath, "w", encoding="utf-8") as f: f.write(txt)
            preview = "\n".join(lines[:min(10, len(lines))])
            await interaction.followup.send(content=f"📄 Exported teams to **{outpath.name}**:\n```\n{preview}\n```", file=discord.File(str(outpath), filename=outpath.name), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"⚠️ Failed to write export file: {e}", ephemeral=True)


    @app_commands.command(name="sangmove", description="Move users from Matchmaking VC to their auto-created team VCs.")
    @app_commands.checks.has_any_role("Administrators", "Clan Staff", "Senior Staff", "Staff", "Trial Staff")
    async def sangmove(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        global last_generated_teams
        teams = last_generated_teams
        if not teams:
            await interaction.followup.send("⚠️ No teams have been generated. Run `/sangmatch` first.", ephemeral=True)
            return
            
        guild = interaction.guild
        category = guild.get_channel(SANG_VC_CATEGORY_ID)
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.followup.send("⚠️ Could not find the Sanguine VC category.", ephemeral=True)
            return
            
        matchmaking_vc = self.bot.get_channel(SANG_MATCHMAKING_VC_ID)
        if not matchmaking_vc or not isinstance(matchmaking_vc, discord.VoiceChannel):
            await interaction.followup.send("⚠️ Could not find the Matchmaking VC.", ephemeral=True)
            return
            
        members_in_matchmaking_vc = matchmaking_vc.members
        team_vcs = {vc.name: vc for vc in category.voice_channels if vc.name.startswith("SanSat")}
                
        if not team_vcs:
            await interaction.followup.send("⚠️ No `SanSat...` voice channels found in the category. Run `/sangmatch` to create them.", ephemeral=True)
            return
            
        moved_count, failed_count = 0, 0
        summary = []

        for i, team in enumerate(teams):
            if not team: continue
            anchor_name = sanitize_nickname(team[0].get("user_name", f"Team{i+1}"))
            vc_name = f"SanSat{anchor_name}"
            target_vc = team_vcs.get(vc_name)

            if not target_vc:
                summary.append(f"❌ Could not find VC named `{vc_name}` for Team {i+1}.")
                failed_count += len(team)
                continue
                
            summary.append(f"✅ Moving Team {i+1} ({anchor_name}) to {target_vc.mention}...")
            
            for player in team:
                try:
                    player_id = int(player["user_id"])
                    member_to_move = next((m for m in members_in_matchmaking_vc if m.id == player_id), None)
                    
                    if member_to_move:
                        await member_to_move.move_to(target_vc, reason="SangMove command")
                        moved_count += 1
                    else:
                        failed_count += 1
                except discord.Forbidden:
                    summary.append(f"  - 🚫 No permission to move {player['user_name']}.")
                    failed_count += 1
                except Exception as e:
                    summary.append(f"  - ⚠️ Error moving {player['user_name']}: {e}")
                    failed_count += 1

        summary_message = f"**Move Complete**\n- Moved {moved_count} members.\n- Failed to move {failed_count} members.\n\n" + "\n".join(summary)
        if len(summary_message) > 1900: summary_message = summary_message[:1900] + "\n... (message trimmed)"
        await interaction.followup.send(summary_message, ephemeral=True)

    @app_commands.command(name="sangcleanup", description="Delete auto-created SanguineSaturday voice channels from the last run.")
    @app_commands.checks.has_any_role("Administrators", "Clan Staff", "Senior Staff", "Staff", "Trial Staff")
    async def sangcleanup(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        category = interaction.guild.get_channel(SANG_VC_CATEGORY_ID)
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.followup.send("⚠️ Category not found.", ephemeral=True); return
            
        deleted, failed = 0, 0
        summary = []
        channels_to_delete = [ch for ch in category.voice_channels if ch.name.startswith("SanSat")]
                
        if not channels_to_delete:
            await interaction.followup.send("🧹 No `SanSat...` voice channels found to delete.", ephemeral=True)
            return
            
        summary.append(f"Found {len(channels_to_delete)} channels to delete...")

        for ch in channels_to_delete:
            try:
                await ch.delete(reason="sangcleanup command")
                summary.append(f"  - Deleted {ch.name}")
                deleted += 1
            except discord.Forbidden:
                summary.append(f"  - 🚫 No permission to delete {ch.name}.")
                failed += 1
            except Exception as e:
                summary.append(f"  - ⚠️ Error deleting {ch.name}: {e}")
                failed += 1
                
        final_message = f"**Cleanup Complete**\n- ✅ Deleted {deleted} channels.\n- ❌ Failed to delete {failed} channels.\n\n" + "\n".join(summary)
        if len(final_message) > 1900: final_message = final_message[:1900] + "\n... (message trimmed)"
        await interaction.followup.send(final_message, ephemeral=True)

    @app_commands.command(name="sangsetmessage", description="Manually set the message ID for the live signup embed.")
    @app_commands.checks.has_role(STAFF_ROLE_ID)
    async def sangsetmessage(self, interaction: discord.Interaction, message_id: str):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try: mid = int(message_id)
        except ValueError:
            await interaction.followup.send("⚠️ That doesn't look like a valid message ID.", ephemeral=True); return

        channel = self.bot.get_channel(SANG_CHANNEL_ID)
        if not channel:
            await interaction.followup.send(f"⚠️ Cannot find channel ID {SANG_CHANNEL_ID}.", ephemeral=True); return
            
        try: await channel.fetch_message(mid)
        except Exception as e:
            await interaction.followup.send(f"⚠️ Could not verify message: {e}", ephemeral=True); return

        await self.save_live_message_id(mid)
        await self.update_live_signup_message()
        await interaction.followup.send(f"✅ Set live signup message to `{mid}` and updated it.", ephemeral=True)

    @app_commands.command(name="sangpostembed", description="Post a new live signup embed and set it as the active one.")
    @app_commands.checks.has_role(STAFF_ROLE_ID)
    async def sangpostembed(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        channel = self.bot.get_channel(SANG_CHANNEL_ID)
        if not channel:
            await interaction.followup.send(f"⚠️ Cannot find channel ID {SANG_CHANNEL_ID}.", ephemeral=True); return
            
        try:
            new_embed = await self._generate_signups_embed()
            live_message = await channel.send(embed=new_embed)
            await self.save_live_message_id(live_message.id)
            await interaction.followup.send(f"✅ Posted new live signup embed (`{live_message.id}`).", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"⚠️ An error occurred: {e}", ephemeral=True)

    @sangsignup.error
    @sangmatch.error
    @sangmatchtest.error
    @sangexport.error
    @sangmove.error
    @sangcleanup.error
    @sangsetmessage.error
    @sangpostembed.error
    async def sang_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingRole):
            await interaction.response.send_message("❌ You don't have the required role for this command.", ephemeral=True)
        else:
            if interaction.response.is_done(): await interaction.followup.send(f"An unexpected error occurred: {error}", ephemeral=True)
            else: await interaction.response.send_message(f"An unexpected error occurred: {error}", ephemeral=True)

    # --- Scheduled Tasks ---

    @tasks.loop(time=dt_time(hour=11, minute=0, tzinfo=CST))
    async def scheduled_post_signup(self):
        day = self.get_event_day()
        target_weekday = 3 if day == "Saturday" else 4
        if datetime.now(CST).weekday() == target_weekday:
            channel = self.bot.get_channel(SANG_CHANNEL_ID)
            if channel: await self.post_signup(channel)

    @tasks.loop(minutes=30)
    async def scheduled_post_reminder(self):
        now = datetime.now(CST)
        day = self.get_event_day()

        if day == "Saturday":
            is_early_reminder = (now.weekday() == 4 and now.hour == 14 and now.minute < 30)
            is_day_of_reminder = (now.weekday() == 5 and now.hour == 13 and now.minute >= 30)
        else: 
            is_early_reminder = (now.weekday() == 5 and now.hour == 14 and now.minute < 30)
            is_day_of_reminder = (now.weekday() == 6 and now.hour == 13 and now.minute >= 30)
        
        if is_early_reminder or is_day_of_reminder:
            channel = self.bot.get_channel(SANG_CHANNEL_ID)
            if channel: await self.post_reminder(channel)

    @tasks.loop(time=dt_time(hour=4, minute=0, tzinfo=CST))
    async def scheduled_clear_sang_sheet(self):
        if datetime.now(CST).weekday() == 0:  # Monday
            if self.sang_sheet:
                try:
                    self.sang_sheet.clear()
                    self.sang_sheet.append_row(SANG_SHEET_HEADER)
                    await self.update_live_signup_message()
                except Exception as e: print(f"🔥 Failed to clear SangSignups sheet: {e}")

    @scheduled_post_signup.before_loop
    @scheduled_post_reminder.before_loop
    @scheduled_clear_sang_sheet.before_loop
    async def before_scheduled_tasks(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(SanguineCog(bot))
