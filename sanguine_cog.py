import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import asyncio
import re
import functools
from discord import ui, ButtonStyle, Member
from discord.ui import View, Button, Modal, TextInput
from typing import Optional, List, Dict, Any, Set
from datetime import datetime, timedelta, timezone, time as dt_time
from zoneinfo import ZoneInfo
import math
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
SENIOR_STAFF_CHANNEL_ID = 1336473990302142484
ADMINISTRATOR_ROLE_ID = 1272961765034164318
SENIOR_STAFF_ROLE_ID = 1336473488159936512
SANG_VC_CATEGORY_ID = 1376645103803830322
SANG_POST_CHANNEL_ID = 1338295765759688767
SANG_MATCHMAKING_VC_ID = 1431953026842624090
SANG_VC_LINK = "https://discord.com/channels/1272629330115297330/1431953026842624090"

SCRIPT_DIR = Path(__file__).parent.resolve()
SANG_MESSAGE_ID_FILE = SCRIPT_DIR / "sang_message_id.txt"

# GSheet Config
SANG_SHEET_ID = "1CCpDAJO7Cq581yF_-rz3vx7L_BTettVaKglSvOmvTOE"
SANG_SHEET_TAB_NAME = "SangSignups"
SANG_HISTORY_TAB_NAME = "History"
SANG_SHEET_HEADER = ["Discord_ID", "Discord_Name", "Favorite Roles", "KC", "Has_Scythe", "Proficiency", "Learning Freeze", "Mentor_Request", "Timestamp", "Blacklist", "Whitelist"]

# Message Content
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
- **Withdraw:** Remove your name from this week's signup list.

The form will remember your answers from past events! 
You only need to edit Kc's and Roles.

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

We will be gathering in the **[Sanguine Sunday VC]({SANG_VC_LINK})**!
We look forward to seeing you there!
"""

# Store last generated teams in memory
last_generated_teams: List[List[Dict[str, Any]]] = []

# ---------------------------
# 🔹 Helper Functions
# ---------------------------
def sanitize_nickname(name: str) -> str:
    """Removes special characters and bot-added tags from display names."""
    if not name:
        return ""
    name = re.sub(r'\s*\([^)]*#\d{4}\)', '', name)
    name = re.sub(r'\s*\[[^\]]*#\d{4}\]', '', name)
    name = re.sub(r'^[!#@]+', '', name)
    return name.strip()

def normalize_role(p: dict) -> str:
    """Standardizes a player's proficiency based on their sheet data."""
    prof = str(p.get("proficiency","")).strip().lower()
    if prof == "mentor":
        return "mentor"
    try:
        kc = int(p.get("kc") or p.get("KC") or 0)
    except Exception:
        return prof
    if kc <= 25: return "new"
    if 26 <= kc <= 49: return "learner"
    if 50 <= kc <= 100: return "proficient"
    return "highly proficient"

PROF_ORDER = {"mentor": 0, "highly proficient": 1, "proficient": 2, "learner": 3, "new": 4}

# Helpers list - prioritized for mentor/learner teams
HELPERS = [
    "lukap42", "antidrop", "robotson", "box man", "redeemed",
    "mr fk", "ms fk", "lube is best", "hazy jane", "lasix",
    "kodai", "lionelious",
]

def prof_rank(p: dict) -> int:
    return PROF_ORDER.get(normalize_role(p), 99)

def scythe_icon(p: dict) -> str:
    return " • <:tob:1272864087105208364>" if p.get("has_scythe") else ""

def freeze_icon(p: dict) -> str:
    return " • ❄️" if p.get("learning_freeze") else ""

def is_proficient_plus(p: dict) -> bool:
    role = normalize_role(p)
    return role in ("mentor", "highly proficient", "proficient")

def is_helper(p: dict) -> bool:
    name = p.get("user_name", "").lower().strip()
    name = re.sub(r'^[!#@*]+', '', name).strip()
    return name in HELPERS

def parse_roles(roles_str: str) -> (bool, bool):
    if not roles_str or roles_str == "N/A":
        return False, False
    roles_str = roles_str.lower()
    knows_range = any(s in roles_str for s in ["range", "ranger", "rdps"])
    knows_melee = any(s in roles_str for s in ["melee", "mdps", "meleer"])
    return knows_range, knows_melee

def is_blacklist_violation(player: Dict[str, Any], team: List[Dict[str, Any]]) -> bool:
    """Checks if a player joining a team violates any blacklists."""
    player_blacklist = player.get("blacklist", set())
    player_id_str = str(player.get("user_id"))

    for p_in_team in team:
        p_in_team_id_str = str(p_in_team.get("user_id"))
        if p_in_team_id_str in player_blacklist:
            return True 
        p_in_team_blacklist = p_in_team.get("blacklist", set())
        if player_id_str in p_in_team_blacklist:
            return True 
    return False

def check_merge_blacklist(clique_to_add: List[Dict], current_team: List[Dict]) -> bool:
    """Checks entire clique against entire team for blacklists."""
    for new_p in clique_to_add:
        if is_blacklist_violation(new_p, current_team):
            return True # Conflict found
    for exist_p in current_team:
        if is_blacklist_violation(exist_p, clique_to_add):
            return True
    return False

def get_cliques(available_raiders: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """Groups players into cliques based on mutual whitelists (Connected Components) using BFS."""
    if not available_raiders:
        return []

    # Map user_id -> player dict
    player_map = {str(p["user_id"]): p for p in available_raiders}
    adjacency = {uid: set() for uid in player_map}

    # Build graph edges
    for p1 in available_raiders:
        id1 = str(p1["user_id"])
        whitelist1 = p1.get("whitelist", set())
        for id2 in whitelist1:
            if id2 in player_map and id2 != id1:
                # Add edge if id2 exists in pool. 
                # Treating as undirected: if A lists B, we link them.
                adjacency[id1].add(id2)
                adjacency[id2].add(id1)

    visited = set()
    cliques = []

    for uid in player_map:
        if uid not in visited:
            # BFS traversal
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
            
            # Sort component members internally by rank
            component.sort(key=prof_rank)
            cliques.append(component)

    return cliques

def matchmaking_algorithm(available_raiders: List[Dict[str, Any]]):
    """
    Robust Matchmaking Algorithm:
    1. Group into atomic units (cliques).
    2. Build Mentor Teams base.
    3. Assign Learners/New to Mentor Teams (Max 4 size preferred, strict requirement).
    4. Assign 1 Helper to each Mentor Team if possible. (Fallback to HP if no helper).
    5. Fill Mentor Teams to size 4/5.
    6. Balance Standard Teams (Size 4 preferred, distribute remainder evenly).
    """
    if not available_raiders:
        return [], []

    print(f"\n🧩 Starting Matchmaking for {len(available_raiders)} players...")

    # --- Step 1: Group into Cliques ---
    cliques = get_cliques(available_raiders)
    
    # Categorize Cliques
    mentor_cliques = []
    learner_cliques = []
    helper_cliques = []
    regular_cliques = []

    for clique in cliques:
        roles = [normalize_role(p) for p in clique]
        has_mentor = "mentor" in roles
        has_learner = "learner" in roles or "new" in roles
        has_helper = any(is_helper(p) for p in clique)

        if has_mentor:
            mentor_cliques.append(clique)
        elif has_learner:
            learner_cliques.append(clique)
        elif has_helper:
            helper_cliques.append(clique)
        else:
            regular_cliques.append(clique)

    # Sort cliques for priority
    # Mentors: Smaller first (easier to build around)
    mentor_cliques.sort(key=len)
    # Learners: New players first
    learner_cliques.sort(key=lambda c: any(normalize_role(p) == "new" for p in c), reverse=True)
    # Helpers: Higher KC first
    helper_cliques.sort(key=lambda c: max(int(p.get("kc", 0)) for p in c), reverse=True)
    # Regulars: Sort by HP presence, then KC
    regular_cliques.sort(key=lambda c: (
        1 if any(normalize_role(p) == "highly proficient" for p in c) else 0,
        max(int(p.get("kc", 0)) for p in c)
    ), reverse=True)

    teams = []
    stranded = []
    
    # Track used cliques by memory ID
    used_cliques = set()
    def mark_used(c): used_cliques.add(id(c))
    def is_used(c): return id(c) in used_cliques

    # ==========================================================
    # PHASE 1: Initialize Mentor Teams
    # ==========================================================
    print("\n🎓 PHASE 1: Initializing Mentor Teams...")
    for m_clique in mentor_cliques:
        teams.append(list(m_clique))
        mark_used(m_clique)

    # ==========================================================
    # PHASE 2: Assign Learners (Priority: Mentor Teams)
    # ==========================================================
    print("\n👶 PHASE 2: Assigning Learners...")
    for l_clique in learner_cliques:
        best_team_idx = -1
        min_size = 999

        # Find best fitting mentor team
        for i, team in enumerate(teams):
            # Constraint: Must be a mentor team
            if not any(normalize_role(p) == "mentor" for p in team):
                continue
            
            # Constraint: Size. Prefer keeping size <= 4 initially. 
            if len(team) + len(l_clique) > 4: 
                continue
            
            # Constraint: Blacklist
            if check_merge_blacklist(l_clique, team):
                continue
            
            # Metric: Pick team with fewest people to spread load
            if len(team) < min_size:
                min_size = len(team)
                best_team_idx = i
        
        if best_team_idx != -1:
            teams[best_team_idx].extend(l_clique)
            mark_used(l_clique)
            print(f"   Mapped Learner Group to Team {best_team_idx+1}")
        else:
            # Cannot fit learner into any mentor team (Full or Blacklisted)
            # STRANDED. Do not put them in standard teams.
            for p in l_clique:
                stranded.append(p)
            mark_used(l_clique)

    # ==========================================================
    # PHASE 3: Assign Support (Helper -> HP)
    # ==========================================================
    print("\n🛡️ PHASE 3: Assigning Support (Helper -> HP)...")
    
    # Identify Mentor+Learner teams that need support
    # Criteria: Mentor + Learner present, but no Helper/HP yet (besides Mentor)
    
    teams_needing_support_indices = []
    for i, team in enumerate(teams):
        has_mentor = any(normalize_role(p) == "mentor" for p in team)
        has_learner = any(normalize_role(p) in ("new", "learner") for p in team)
        
        # Check if already has strong support (Helper OR HP)
        has_strong_support = False
        for p in team:
            if is_helper(p) or normalize_role(p) == "highly proficient":
                # Don't count the mentor as the "support" slot if they are the only one
                # But normalize_role "mentor" returns "mentor", so this check is safe
                has_strong_support = True
                
        if has_mentor and has_learner and not has_strong_support:
             teams_needing_support_indices.append(i)

    # Attempt to fill with Helpers first
    for t_idx in teams_needing_support_indices:
        team = teams[t_idx]
        filled = False
        
        # Look in helper_cliques first
        for h_clique in helper_cliques:
            if is_used(h_clique): continue
            
            if len(team) + len(h_clique) <= 5: # Allow 5 to ensure support
                if not check_merge_blacklist(h_clique, team):
                    team.extend(h_clique)
                    mark_used(h_clique)
                    filled = True
                    break
        
        # If no helper found, look for HP in regular_cliques
        if not filled:
            for r_clique in regular_cliques:
                if is_used(r_clique): continue
                
                # Check if clique contains HP
                has_hp = any(normalize_role(p) == "highly proficient" for p in r_clique)
                if has_hp:
                    if len(team) + len(r_clique) <= 5:
                         if not check_merge_blacklist(r_clique, team):
                            team.extend(r_clique)
                            mark_used(r_clique)
                            filled = True
                            print(f"   Assigned HP fallback to Team {t_idx+1}")
                            break

    # ==========================================================
    # PHASE 4: Fill Mentor Teams & Consolidate Remaining
    # ==========================================================
    print("\n⚖️ PHASE 4: Filling & Balancing...")
    remaining_cliques = []
    
    for c in helper_cliques:
        if not is_used(c): remaining_cliques.append(c)
    for c in regular_cliques:
        if not is_used(c): remaining_cliques.append(c)

    # Sort remaining by size (smallest first to fill gaps)
    remaining_cliques.sort(key=len) 
    
    changed = True
    while changed:
        changed = False
        for i in range(len(remaining_cliques)):
            if is_used(remaining_cliques[i]): continue
            
            clique = remaining_cliques[i]
            assigned = False
            
            # Look for mentor team < 4
            for t_idx, team in enumerate(teams):
                has_mentor = any(normalize_role(p) == "mentor" for p in team)
                if has_mentor and len(team) < 4:
                    if len(team) + len(clique) <= 5: 
                         if not check_merge_blacklist(clique, team):
                            team.extend(clique)
                            mark_used(clique)
                            assigned = True
                            changed = True
                            break
            if assigned: break

    # ==========================================================
    # PHASE 5: Standard Teams (Balancing Remainder)
    # ==========================================================
    pool_cliques = [c for c in remaining_cliques if not is_used(c)]
    
    if pool_cliques:
        total_players = sum(len(c) for c in pool_cliques)
        
        num_teams = round(total_players / 4)
        if num_teams == 0: num_teams = 1
        
        if num_teams > 1 and (total_players / num_teams) < 3:
            num_teams -= 1
            
        new_teams = [[] for _ in range(num_teams)]
        
        # Sort pool by KC descending
        pool_cliques.sort(key=lambda c: max(int(p.get("kc",0)) for p in c), reverse=True)
        
        for clique in pool_cliques:
            # Pick team with fewest players
            valid_indices = []
            for i, t in enumerate(new_teams):
                if not check_merge_blacklist(clique, t):
                    valid_indices.append(i)
            
            if not valid_indices:
                for p in clique: stranded.append(p)
                continue
            
            # Sort valid teams by current size (ascending)
            valid_indices.sort(key=lambda i: len(new_teams[i]))
            
            target = valid_indices[0]
            new_teams[target].extend(clique)
            
        teams.extend([t for t in new_teams if t])

    # Final cleanup of empty teams
    teams = [t for t in teams if t]
    
    print(f"\n✅ Result: {len(teams)} Teams, {len(stranded)} Stranded.")
    return teams, stranded

def format_player_line_plain(guild: discord.Guild, p: dict) -> str:
    nickname = p.get("user_name") or "Unknown"
    role_text = p.get("proficiency", "Unknown").replace(" ", "-").capitalize().replace("-", " ")
    kc_raw = p.get("kc", 0)
    kc_text = f"({kc_raw} KC)" if isinstance(kc_raw, int) and kc_raw > 0 and role_text != "Mentor" and kc_raw != 9999 else ""
    scythe = scythe_icon(p)
    freeze = freeze_icon(p)
    return f"{nickname} • **{role_text}** {kc_text}{scythe}{freeze}"

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
    return f"{mention} • **{role_text}** {kc_text}{scythe}{freeze}"

# ---------------------------
# 🔹 UI Modals & Views
# ---------------------------

class UserSignupForm(Modal, title="Sanguine Sunday Signup"):
    roles_known = TextInput(label="Favorite Roles (Leave blank if None)", placeholder="Inputs: All, Nfrz, Sfrz, Mdps, Rdps", style=discord.TextStyle.short, max_length=4, required=False)
    kc = TextInput(label="What is your Normal Mode ToB KC?", placeholder="0-10 = New, 11-25 = Learner, 26-100 = Proficient, 100+ = Highly Proficient", style=discord.TextStyle.short, max_length=5, required=True)
    has_scythe = TextInput(label="Do you have a Scythe? (Yes/No)", placeholder="Yes or No ONLY", style=discord.TextStyle.short, max_length=3, required=True)
    learning_freeze = TextInput(label="Learn freeze role? (Yes or leave blank)", placeholder="Yes or blank/No ONLY", style=discord.TextStyle.short, max_length=3, required=False)
    wants_mentor = TextInput(label="Do you want assistance from a Mentor?", placeholder="Yes or No/Blank", style=discord.TextStyle.short, max_length=3, required=False)

    def __init__(self, cog: 'SanguineCog', previous_data: dict = None):
        super().__init__(title="Sanguine Sunday Signup")
        self.cog = cog
        self.previous_data = previous_data 
        if previous_data:
            self.roles_known.default = previous_data.get("Favorite Roles", "")
            kc_val = previous_data.get("KC", "")
            self.kc.default = str(kc_val) if kc_val not in ["", None, "X"] else ""
            self.has_scythe.default = "Yes" if previous_data.get("Has_Scythe", False) else "No"
            self.learning_freeze.default = "Yes" if previous_data.get("Learning Freeze", False) else ""
            self.wants_mentor.default = "Yes" if previous_data.get("Mentor_Request", False) else ""
        
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        if not self.cog.sang_sheet:
            await interaction.followup.send("⚠️ Error: The Sanguine Sunday signup sheet is not connected. Please contact staff.", ephemeral=True)
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

        proficiency_value = ""
        if kc_value <= 10: proficiency_value = "New"
        elif 11 <= kc_value <= 49: proficiency_value = "Learner"
        elif 50 <= kc_value <= 100: proficiency_value = "Proficient"
        else: proficiency_value = "Highly Proficient"

        roles_known_value = str(self.roles_known).strip() or "None"
        learning_freeze_value = str(self.learning_freeze).strip().lower()
        learning_freeze_bool = learning_freeze_value in ["yes", "y"]
        wants_mentor_value = str(self.wants_mentor).strip().lower()
        wants_mentor_bool = wants_mentor_value in ["yes", "y"]

        user_id = str(interaction.user.id)
        user_name = sanitize_nickname(interaction.user.display_name)
        timestamp = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S")
        
        blacklist_value = self.previous_data.get("Blacklist", "") if self.previous_data else ""
        whitelist_value = self.previous_data.get("Whitelist", "") if self.previous_data else ""

        row_data = [user_id, user_name, roles_known_value, kc_value, has_scythe_bool, proficiency_value, learning_freeze_bool, wants_mentor_bool, timestamp, blacklist_value, whitelist_value]
        
        try:
            sang_sheet_success, history_sheet_success = await self.cog._write_to_sheets_in_thread(user_id, row_data)

            if sang_sheet_success and history_sheet_success:
                await interaction.followup.send(
                    f"✅ **You are signed up as {proficiency_value}!**\n"
                    f"**KC:** {kc_value}\n"
                    f"**Scythe:** {'Yes' if has_scythe_bool else 'No'}\n"
                    f"**Favorite Roles:** {roles_known_value}\n"
                    f"**Learn Freeze:** {'Yes' if learning_freeze_bool else 'No'}\n"
                    f"**Mentor Request:** {'Yes' if wants_mentor_bool else 'No'}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send("⚠️ An error occurred while saving your signup. Please contact staff.", ephemeral=True)
        except Exception as e:
            print(f"🔥🔥🔥 UNCAUGHT ERROR IN UserSignupForm on_submit: {e}")
            await interaction.followup.send("⚠️ A critical error occurred. Please tell staff to check the bot console.", ephemeral=True)


class MentorSignupForm(Modal, title="Sanguine Sunday Mentor Signup"):
    roles_known = TextInput(label="Favorite Roles (Leave blank if None)", placeholder="Inputs: All, Nfrz, Sfrz, Mdps, Rdps", style=discord.TextStyle.short, max_length=4, required=True)
    kc = TextInput(label="What is your Normal Mode ToB KC?", placeholder="150+", style=discord.TextStyle.short, max_length=5, required=True)
    has_scythe = TextInput(label="Do you have a Scythe? (Yes/No)", placeholder="Yes or No", style=discord.TextStyle.short, max_length=3, required=True)

    def __init__(self, cog: 'SanguineCog', previous_data: dict = None):
        super().__init__(title="Sanguine Sunday Mentor Signup")
        self.cog = cog
        self.previous_data = previous_data
        if previous_data:
                 self.roles_known.default = previous_data.get("Favorite Roles", "")
                 kc_val = previous_data.get("KC", "")
                 self.kc.default = str(kc_val) if kc_val not in ["", None, "X"] else ""
                 self.has_scythe.default = "Yes" if previous_data.get("Has_Scythe", False) else "No"
        
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        if not self.cog.sang_sheet:
            await interaction.followup.send("⚠️ Error: The Sanguine Sunday signup sheet is not connected.", ephemeral=True)
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

        proficiency_value = "Mentor"
        roles_known_value = str(self.roles_known).strip()
        learning_freeze_bool = False

        user_id = str(interaction.user.id)
        user_name = sanitize_nickname(interaction.user.display_name)
        timestamp = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S")
        
        blacklist_value = self.previous_data.get("Blacklist", "") if self.previous_data else ""
        whitelist_value = self.previous_data.get("Whitelist", "") if self.previous_data else ""

        row_data = [user_id, user_name, roles_known_value, kc_value, has_scythe_bool, proficiency_value, learning_freeze_bool, False, timestamp, blacklist_value, whitelist_value]

        try:
            sang_sheet_success, history_sheet_success = await self.cog._write_to_sheets_in_thread(user_id, row_data)

            if sang_sheet_success and history_sheet_success:
                await interaction.followup.send(
                    f"✅ **You are signed up as a Mentor!**\n"
                    f"**KC:** {kc_value}\n"
                    f"**Scythe:** {'Yes' if has_scythe_bool else 'No'}\n"
                    f"**Favorite Roles:** {roles_known_value}",
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
                await interaction.followup.send(f"✅ **{user_name}**, you have been successfully withdrawn from this week's Sanguine Sunday signups.", ephemeral=True)
                print(f"✅ User {user_id} ({user_name}) withdrew from SangSignups.")
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
            
            try:
                self.sang_sheet = sang_google_sheet.worksheet(SANG_SHEET_TAB_NAME)
                header = self.sang_sheet.row_values(1)
                if header != SANG_SHEET_HEADER:
                    print("⚠️ Sanguine sheet header mismatch. Re-writing...")
                    self.sang_sheet.clear()
                    self.sang_sheet.append_row(SANG_SHEET_HEADER)
            except gspread.exceptions.WorksheetNotFound:
                print(f"'{SANG_SHEET_TAB_NAME}' not found. Creating...")
                self.sang_sheet = sang_google_sheet.add_worksheet(title=SANG_SHEET_TAB_NAME, rows="100", cols="20")
                self.sang_sheet.append_row(SANG_SHEET_HEADER)
            
            try:
                self.history_sheet = sang_google_sheet.worksheet(SANG_HISTORY_TAB_NAME)
                header = self.history_sheet.row_values(1)
                if header != SANG_SHEET_HEADER:
                    print("⚠️ Sanguine history sheet header mismatch. Re-writing...")
                    self.history_sheet.clear()
                    self.history_sheet.append_row(SANG_SHEET_HEADER)
            except gspread.exceptions.WorksheetNotFound:
                print(f"'{SANG_HISTORY_TAB_NAME}' not found. Creating...")
                self.history_sheet = sang_google_sheet.add_worksheet(title=SANG_HISTORY_TAB_NAME, rows="1000", cols="20")
                self.history_sheet.append_row(SANG_SHEET_HEADER)
            
            print("✅ Sanguine Cog: Google Sheets initialized successfully.")
        except Exception as e:
            print(f"🔥 CRITICAL ERROR initializing SanguineCog GSheets: {e}")

        self.bot.add_view(SignupView(self))

    @commands.Cog.listener()
    async def on_ready(self):
        await self.load_live_message_id()
        if not self.scheduled_post_signup.is_running():
            self.scheduled_post_signup.start()
            print("✅ Sanguine Cog: Started scheduled signup task.")
        if not self.scheduled_post_reminder.is_running():
            self.scheduled_post_reminder.start()
            print("✅ Sanguine Cog: Started scheduled reminder task.")
        if not self.scheduled_clear_sang_sheet.is_running():
            self.scheduled_clear_sang_sheet.start()
            print("✅ Sanguine Cog: Started scheduled sheet clear task.")
        print("Sanguine Cog is ready.")

    async def _write_to_sheets_in_thread(self, user_id: str, row_data: List[Any]) -> (bool, bool):
        def _blocking_sheet_write():
            sang_success = False
            hist_success = False
            try:
                cell = self.sang_sheet.find(user_id, in_column=1)
                if cell is None:
                    self.sang_sheet.append_row(row_data)
                else:
                    self.sang_sheet.update(values=[row_data], range_name=f'A{cell.row}:K{cell.row}')
                sang_success = True
            except Exception as e:
                print(f"🔥 GSpread error on SangSignups: {e}")

            if self.history_sheet:
                try:
                    history_cell = self.history_sheet.find(user_id, in_column=1)
                    if history_cell is None:
                        self.history_sheet.append_row(row_data)
                    else:
                        self.history_sheet.update(values=[row_data], range_name=f'A{history_cell.row}:K{history_cell.row}')
                    hist_success = True
                except Exception as e:
                    print(f"🔥 GSpread error on History: {e}")
            else:
                hist_success = True 
            
            return sang_success, hist_success
        
        loop = asyncio.get_running_loop()
        sang_sheet_success, history_sheet_success = await loop.run_in_executor(
            None, _blocking_sheet_write
        )
        if sang_sheet_success:
            await self.update_live_signup_message()
        return sang_sheet_success, history_sheet_success

    async def _withdraw_user_in_thread(self, user_id: str) -> bool:
        def _blocking_sheet_delete():
            try:
                cell = self.sang_sheet.find(user_id, in_column=1)
                if cell is None:
                    return False
                self.sang_sheet.delete_rows(cell.row)
                return True
            except Exception as e:
                print(f"🔥 GSpread error on withdrawal (in thread): {e}")
                raise e 
        
        loop = asyncio.get_running_loop()
        deleted = await loop.run_in_executor(None, _blocking_sheet_delete)
        if deleted:
            await self.update_live_signup_message()
        return deleted

    async def _create_team_embeds(self, teams, title, description, color, guild, format_func):
        embeds = []
        if not teams:
            return embeds
        
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
            
            current_embed.add_field(
                name=f"Team {i} (Size: {len(team)})",
                value="\n".join(lines) if lines else "—",
                inline=False
            )
            field_count += 1
            
        return embeds

    async def _generate_signups_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="<:sanguine_sunday:1388100187985154130> Sanguine Sunday Signups",
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
            print(f"🔥 GSheet error fetching all signups for embed: {e}")
            embed.description = "⚠️ An error occurred while fetching signups."
            return embed
        
        players = []
        # Temporary lists for mentor deficit calculation
        temp_clique_data = [] 

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

            # Reconstruct simplified player obj for cliques and display
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
                "whitelist": whitelist_ids
            }
            players.append(p_data)
            temp_clique_data.append(p_data)
        
        # Calculate Mentor Deficit based on actual Cliques
        try:
            cliques = get_cliques(temp_clique_data)
            learner_cliques_count = 0
            mentor_cliques_count = 0
            
            for clique in cliques:
                roles = [normalize_role(p) for p in clique]
                if "mentor" in roles:
                    mentor_cliques_count += 1
                elif "learner" in roles or "new" in roles:
                    learner_cliques_count += 1
            
            # Logic: We need 1 Mentor Group per Learner Group
            deficit = learner_cliques_count - mentor_cliques_count
            if deficit > 0:
                 embed.description = f"**⚠️ Mentors Needed:** We need **{deficit}** more Mentor(s) to cover all learners!"
            else:
                 embed.description = "✅ Current signups have sufficient Mentor coverage."
        except Exception as e:
            print(f"Error calculating mentor deficit: {e}")

        # Sort and Group for Display
        players.sort(key=prof_rank)
        grouped_players = {}
        for p in players:
            prof = p['proficiency'].capitalize()
            if prof not in grouped_players:
                grouped_players[prof] = []
            grouped_players[prof].append(p)
            
        for prof_key in PROF_ORDER.keys():
            prof_name = prof_key.capitalize()
            if prof_name in grouped_players:
                player_list = grouped_players[prof_name]
                field_value = []
                for p in player_list:
                    scythe = scythe_icon(p)
                    freeze = freeze_icon(p)
                    field_value.append(f"{p['user_name']}{scythe}{freeze}")
                
                embed.add_field(
                    name=f"**{prof_name}** ({len(player_list)})",
                    value="\n".join(field_value),
                    inline=False
                )
                
        embed.set_footer(text=f"Total Signups: {len(players)}")
        return embed

    async def load_live_message_id(self):
        try:
            if SANG_MESSAGE_ID_FILE.exists():
                content = SANG_MESSAGE_ID_FILE.read_text().strip()
                if content:
                    self.live_signup_message_id = int(content)
                    print(f"✅ Loaded live signup message ID: {self.live_signup_message_id}")
                else:
                    self.live_signup_message_id = None
            else:
                self.live_signup_message_id = None
        except Exception as e:
            print(f"🔥 Failed to load live signup message ID: {e}")
            self.live_signup_message_id = None

    async def save_live_message_id(self, message_id: Optional[int]):
        self.live_signup_message_id = message_id
        try:
            if message_id is None:
                SANG_MESSAGE_ID_FILE.unlink(missing_ok=True)
            else:
                SANG_MESSAGE_ID_FILE.write_text(str(message_id))
        except Exception as e:
            print(f"🔥 Failed to save live signup message ID: {e}")

    async def update_live_signup_message(self):
        async with self.live_signup_message_lock:
            if not self.live_signup_message_id:
                return

            new_embed = await self._generate_signups_embed()
            
            try:
                channel = self.bot.get_channel(SANG_CHANNEL_ID)
                if not channel:
                    return
                    
                message = await channel.fetch_message(self.live_signup_message_id)
                await message.edit(embed=new_embed)
                print(f"✅ Updated live signup message: {self.live_signup_message_id}")
            
            except discord.NotFound:
                print(f"🔥 Live signup message {self.live_signup_message_id} not found. Clearing ID.")
                await self.save_live_message_id(None)
            except Exception as e:
                print(f"🔥 Failed to update live signup message: {e}")

    def get_previous_signup(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.history_sheet:
            return None
        try:
            all_records = self.history_sheet.get_all_records()
            if not all_records:
                return None
            
            for record in reversed(all_records):
                sheet_discord_id = record.get("Discord_ID")
                sheet_discord_id_str = str(sheet_discord_id) if sheet_discord_id is not None else None
                
                if sheet_discord_id_str == user_id:
                    record["Has_Scythe"] = str(record.get("Has_Scythe", "FALSE")).upper() == "TRUE"
                    record["Learning Freeze"] = str(record.get("Learning Freeze", "FALSE")).upper() == "TRUE"
                    return record
            return None
        except Exception as e:
            print(f"🔥 GSpread error fetching previous signup for {user_id}: {e}")
            return None

    async def post_signup(self, channel: discord.TextChannel):
        signup_message = await channel.send(SANG_MESSAGE, view=SignupView(self))
        print(f"✅ Posted Sanguine Sunday signup in #{channel.name}")

        try:
            await signup_message.pin()
        except Exception:
            pass

        try:
            initial_embed = await self._generate_signups_embed()
            live_message = await channel.send(embed=initial_embed)
            await self.save_live_message_id(live_message.id)
            print(f"✅ Posted live signup message: {live_message.id}")
        except Exception as e:
            print(f"🔥 Failed to post live signup message: {e}")

    async def post_reminder(self, channel: discord.TextChannel):
        if not self.sang_sheet: return False
        
        try:
            async for message in channel.history(limit=50):
                if message.author == self.bot.user and LEARNER_REMINDER_IDENTIFIER in message.content:
                    await message.delete()
        except Exception: pass

        learners = []
        try:
            all_signups = self.sang_sheet.get_all_records()
            for signup in all_signups:
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
            await self.update_live_signup_message()
            return True
        except Exception as e:
            print(f"🔥 GSpread error fetching/posting reminder: {e}")
            await channel.send("⚠️ Error processing learner list from database.")
            return False

    # --- Slash Commands ---
    
    @app_commands.command(name="sangsignup", description="Manage Sanguine Sunday signups.")
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
            if result:
                await interaction.followup.send(f"✅ Learner reminder posted in {target_channel.mention}.")
            else:
                await interaction.followup.send("⚠️ Could not post the reminder.")

    @app_commands.command(name="sangmatch", description="Create ToB teams from users in the designated voice channel.")
    @app_commands.checks.has_role(STAFF_ROLE_ID)
    async def sangmatch(self, interaction: discord.Interaction):
        if not self.sang_sheet:
            await interaction.response.send_message("⚠️ Error: The Sanguine Sunday sheet is not connected.", ephemeral=True)
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
            print(f"🔥 GSheet error fetching all signups: {e}")
            await interaction.followup.send("⚠️ An error occurred fetching signups from the database.")
            return

        available_raiders = []
        for signup in all_signups_records:
            user_id = str(signup.get("Discord_ID"))
            if vc_member_ids and user_id not in vc_member_ids:
                continue
            
            roles_str = signup.get("Favorite Roles", "")
            knows_range, knows_melee = parse_roles(roles_str)
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
                "has_scythe": str(signup.get("Has_Scythe", "FALSE")).upper() == "TRUE",
                "roles_known": roles_str,
                "learning_freeze": str(signup.get("Learning Freeze", "FALSE")).upper() == "TRUE",
                "knows_range": knows_range,
                "knows_melee": knows_melee,
                "wants_mentor": str(signup.get("Mentor_Request", "FALSE")).upper() == "TRUE",
                "blacklist": blacklist_ids,
                "whitelist": whitelist_ids
            })

        if not available_raiders:
            await interaction.followup.send(f"⚠️ None of the users in {voice_channel.mention} have signed up for the event." if voice_channel else "⚠️ No eligible signups.")
            return

        teams, stranded_players = matchmaking_algorithm(available_raiders)

        guild = interaction.guild
        category = guild.get_channel(SANG_VC_CATEGORY_ID)
        created_vcs = []
        
        if category and isinstance(category, discord.CategoryChannel):
            member_role = guild.get_role(MEMBER_ROLE_ID)
            overwrites = {}
            if member_role:
                overwrites[member_role] = discord.PermissionOverwrite(view_channel=True, connect=True, speak=True)

            for i, team in enumerate(teams):
                try:
                    mentor_name = f"Team{i+1}"
                    if team: 
                        mentor_name = sanitize_nickname(team[0].get("user_name", mentor_name))

                    vc_name = f"SanSun{mentor_name}"
                    new_vc = await category.create_voice_channel(name=vc_name, overwrites=overwrites)
                    created_vcs.append(new_vc)
                except Exception as e:
                    print(f"Error creating VC: {e}") 

        post_channel = interaction.channel
        
        embed_title = f"Sanguine Sunday Teams - {channel_name}"
        embed_desc = f"Created {len(teams)} valid team(s) from {len(available_raiders)} available signed-up users."
        if stranded_players:
            embed_desc += f"\n⚠️ **Stranded Players:** {', '.join([p['user_name'] for p in stranded_players])}"
        
        team_embeds = await self._create_team_embeds(
            teams,
            embed_title,
            embed_desc,
            discord.Color.red(),
            guild,
            format_player_line_mention
        )
        
        global last_generated_teams
        last_generated_teams = teams

        for i, embed in enumerate(team_embeds):
            if i == 0:
                await interaction.followup.send(embed=embed)
            else:
                await post_channel.send(embed=embed)
        
    @app_commands.command(name="sangmatchtest", description="Create ToB teams without pinging or creating voice channels; show plain-text nicknames.")
    @app_commands.checks.has_role(STAFF_ROLE_ID)
    @app_commands.describe(voice_channel="Optional: The voice channel to pull users from. If omitted, uses all signups.", channel="(Optional) Override the text channel to post teams (testing).")
    async def sangmatchtest(self, interaction: discord.Interaction, voice_channel: Optional[discord.VoiceChannel] = None, channel: Optional[discord.TextChannel] = None):
        if not self.sang_sheet:
            await interaction.response.send_message("⚠️ Error: The Sanguine Sunday sheet is not connected.", ephemeral=True)
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

        try:
            all_signups_records = self.sang_sheet.get_all_records()
        except Exception as e:
            await interaction.followup.send("⚠️ An error occurred fetching signups from the database.")
            return
        
        available_raiders = []
        for signup in all_signups_records:
            user_id = str(signup.get("Discord_ID"))
            if vc_member_ids and user_id not in vc_member_ids: continue
            
            roles_str = signup.get("Favorite Roles", "")
            knows_range, knows_melee = parse_roles(roles_str)
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
                "proficiency": proficiency_val, "kc": kc_val,
                "has_scythe": str(signup.get("Has_Scythe", "FALSE")).upper() == "TRUE",
                "roles_known": roles_str, "learning_freeze": str(signup.get("Learning Freeze", "FALSE")).upper() == "TRUE",
                "knows_range": knows_range, "knows_melee": knows_melee,
                "wants_mentor": str(signup.get("Mentor_Request", "FALSE")).upper() == "TRUE",
                "blacklist": blacklist_ids,
                "whitelist": whitelist_ids
            })

        if not available_raiders:
            await interaction.followup.send("⚠️ No eligible signups.")
            return

        teams, stranded_players = matchmaking_algorithm(available_raiders)

        guild = interaction.guild
        post_channel = channel or interaction.channel

        embed_title = f"Sanguine Sunday Teams (Test, no pings/VC) - {channel_name}"
        embed_desc = f"Created {len(teams)} valid team(s) from {len(available_raiders)} available signed-up users."
        if stranded_players:
            embed_desc += f"\n⚠️ **Stranded Players:** {', '.join([p['user_name'] for p in stranded_players])}"

        team_embeds = await self._create_team_embeds(
            teams,
            embed_title,
            embed_desc,
            discord.Color.dark_gray(),
            guild,
            format_player_line_plain
        )

        global last_generated_teams
        last_generated_teams = teams
        
        for i, embed in enumerate(team_embeds):
            if i == 0 and interaction.channel == post_channel:
                await interaction.followup.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
            else:
                await post_channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        
        if interaction.channel != post_channel:
             await interaction.followup.send("✅ Posted no-ping test teams (no voice channels created).", ephemeral=True)

    @app_commands.command(name="sangexport", description="Export the most recently generated teams to a text file.")
    @app_commands.checks.has_any_role("Administrators", "Clan Staff", "Senior Staff", "Staff", "Trial Staff")
    async def sangexport(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        global last_generated_teams
        teams = last_generated_teams
        if not teams:
            await interaction.followup.send("⚠️ No teams found from this session.", ephemeral=True)
            return

        guild = interaction.guild
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
        try:
            export_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            export_dir = Path("/tmp")
            export_dir.mkdir(parents=True, exist_ok=True)
        
        ts = datetime.now(CST).strftime("%Y%m%d_%H%M%S")
        outpath = export_dir / f"sanguine_teams_{ts}.txt"
        
        try:
            with open(outpath, "w", encoding="utf-8") as f:
                f.write(txt)
            
            preview = "\n".join(lines[:min(10, len(lines))])
            await interaction.followup.send(content=f"📄 Exported teams to **{outpath.name}**:\n```\n{preview}\n```", file=discord.File(str(outpath), filename=outpath.name), ephemeral=True)
        except Exception as e:
            print(f"🔥 Failed to write or send export file: {e}")
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
            
        team_vcs = {}
        for vc in category.voice_channels:
            if vc.name.startswith("SanSun"):
                team_vcs[vc.name] = vc
                
        if not team_vcs:
            await interaction.followup.send("⚠️ No `SanSun...` voice channels found in the category. Run `/sangmatch` to create them.", ephemeral=True)
            return
            
        moved_count = 0
        failed_count = 0
        summary = []

        for i, team in enumerate(teams):
            if not team:
                continue
                
            anchor_name = sanitize_nickname(team[0].get("user_name", f"Team{i+1}"))
            vc_name = f"SanSun{anchor_name}"
            target_vc = team_vcs.get(vc_name)

            if not target_vc:
                summary.append(f"❌ Could not find VC named `{vc_name}` for Team {i+1}.")
                failed_count += len(team)
                continue
                
            summary.append(f"✅ Moving Team {i+1} ({anchor_name}) to {target_vc.mention}...")
            
            for player in team:
                try:
                    player_id = int(player["user_id"])
                    
                    member_to_move = None
                    for member in members_in_matchmaking_vc:
                        if member.id == player_id:
                            member_to_move = member
                            break
                    
                    if member_to_move:
                        await member_to_move.move_to(target_vc, reason="SangMove command")
                        moved_count += 1
                    else:
                        print(f"Player {player['user_name']} ({player_id}) not in matchmaking VC.")
                        failed_count += 1
                except discord.Forbidden:
                    summary.append(f"  - 🚫 No permission to move {player['user_name']}.")
                    failed_count += 1
                except Exception as e:
                    summary.append(f"  - ⚠️ Error moving {player['user_name']}: {e}")
                    failed_count += 1

        summary_message = f"**Move Complete**\n- Moved {moved_count} members.\n- Failed to move {failed_count} members.\n\n"
        summary_message += "\n".join(summary)
        
        if len(summary_message) > 1900:
            summary_message = summary_message[:1900] + "\n... (message trimmed)"
            
        await interaction.followup.send(summary_message, ephemeral=True)

    @app_commands.command(name="sangcleanup", description="Delete auto-created SanguineSunday voice channels from the last run.")
    @app_commands.checks.has_any_role("Administrators", "Clan Staff", "Senior Staff", "Staff", "Trial Staff")
    async def sangcleanup(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild
        category = guild.get_channel(SANG_VC_CATEGORY_ID)
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.followup.send("⚠️ Category not found.", ephemeral=True); return
            
        deleted = 0
        failed = 0
        summary = []
        
        channels_to_delete = []
        for ch in category.voice_channels:
            if ch.name.startswith("SanSun"):
                channels_to_delete.append(ch)
                
        if not channels_to_delete:
            await interaction.followup.send("🧹 No `SanSun...` voice channels found to delete.", ephemeral=True)
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
                
        final_message = f"**Cleanup Complete**\n- ✅ Deleted {deleted} channels.\n- ❌ Failed to delete {failed} channels.\n\n"
        final_message += "\n".join(summary)
        
        if len(final_message) > 1900:
            final_message = final_message[:1900] + "\n... (message trimmed)"

        await interaction.followup.send(final_message, ephemeral=True)


    @app_commands.command(name="sangsetmessage", description="Manually set the message ID for the live signup embed.")
    @app_commands.checks.has_role(STAFF_ROLE_ID)
    @app_commands.describe(message_id="The Message ID of the embed to update.")
    async def sangsetmessage(self, interaction: discord.Interaction, message_id: str):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        try:
            mid = int(message_id)
        except ValueError:
            await interaction.followup.send("⚠️ That doesn't look like a valid message ID. It should be a long number.", ephemeral=True)
            return

        channel = self.bot.get_channel(SANG_CHANNEL_ID)
        if not channel:
            await interaction.followup.send(f"⚠️ Cannot find channel ID {SANG_CHANNEL_ID}.", ephemeral=True)
            return
            
        try:
            await channel.fetch_message(mid)
        except discord.NotFound:
            await interaction.followup.send(f"⚠️ Could not find a message with that ID in {channel.mention}.", ephemeral=True)
            return
        except discord.Forbidden:
            await interaction.followup.send(f"⚠️ I don't have permission to see that message. Check my permissions in {channel.mention}.", ephemeral=True)
            return
        except Exception as e:
            await interaction.followup.send(f"⚠️ An unknown error occurred while verifying the message: {e}", ephemeral=True)
            return

        await self.save_live_message_id(mid)
        await self.update_live_signup_message()

        await interaction.followup.send(
            f"✅ Set live signup message to `{mid}`.\n"
            f"I've updated it with the current signups.",
            ephemeral=True
        )

    @app_commands.command(name="sangpostembed", description="Post a new live signup embed and set it as the active one.")
    @app_commands.checks.has_role(STAFF_ROLE_ID)
    async def sangpostembed(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        channel = self.bot.get_channel(SANG_CHANNEL_ID)
        if not channel:
            await interaction.followup.send(f"⚠️ Cannot find channel ID {SANG_CHANNEL_ID}.", ephemeral=True)
            return
            
        try:
            new_embed = await self._generate_signups_embed()
            live_message = await channel.send(embed=new_embed)
            await self.save_live_message_id(live_message.id)
            
            await interaction.followup.send(
                f"✅ Posted new live signup embed in {channel.mention}.\n"
                f"This message (`{live_message.id}`) will now be updated automatically.",
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.followup.send(f"⚠️ I don't have permission to post messages in {channel.mention}.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"⚠️ An unknown error occurred: {e}", ephemeral=True)


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
            print(f"Error in a Sanguine command: {error}")
            if interaction.response.is_done():
                await interaction.followup.send(f"An unexpected error occurred: {error}", ephemeral=True)
            else:
                await interaction.response.send_message(f"An unexpected error occurred: {error}", ephemeral=True)

    # --- Scheduled Tasks ---

    @tasks.loop(time=dt_time(hour=11, minute=0, tzinfo=CST))
    async def scheduled_post_signup(self):
        if datetime.now(CST).weekday() == 4:  # 4 = Friday
            print("It's Friday at 11:00 AM CST. Posting Sanguine signup...")
            channel = self.bot.get_channel(SANG_CHANNEL_ID)
            if channel:
                await self.post_signup(channel)
            else:
                print(f"🔥 Failed to post signup: Channel {SANG_CHANNEL_ID} not found.")

    @tasks.loop(minutes=30)
    async def scheduled_post_reminder(self):
        now = datetime.now(CST)
        is_saturday_reminder = (now.weekday() == 5 and now.hour == 14 and now.minute < 30)
        is_sunday_reminder = (now.weekday() == 6 and now.hour == 13 and now.minute >= 30)

        if is_saturday_reminder or is_sunday_reminder:
            if is_saturday_reminder:
                print("It's Saturday at 2:00 PM CST. Posting Sanguine learner reminder...")
            if is_sunday_reminder:
                print("It's Sunday at 1:30 PM CST. Posting Sanguine learner reminder...")
                
            channel = self.bot.get_channel(SANG_CHANNEL_ID)
            if channel:
                await self.post_reminder(channel)
            else:
                print(f"🔥 Failed to post reminder: Channel {SANG_CHANNEL_ID} not found.")

    @tasks.loop(time=dt_time(hour=4, minute=0, tzinfo=CST)) # 4 AM CST
    async def scheduled_clear_sang_sheet(self):
        if datetime.now(CST).weekday() == 0:  # 0 = Monday
            print("MONDAY DETECTED: Clearing SangSignups sheet...")
            if self.sang_sheet:
                try:
                    self.sang_sheet.clear()
                    self.sang_sheet.append_row(SANG_SHEET_HEADER)
                    print("✅ SangSignups sheet cleared and headers added.")
                    await self.update_live_signup_message()
                except Exception as e:
                    print(f"🔥 Failed to clear SangSignups sheet: {e}")
            else:
                print("⚠️ Cannot clear SangSignups sheet, not connected.")

    @scheduled_post_signup.before_loop
    @scheduled_post_reminder.before_loop
    @scheduled_clear_sang_sheet.before_loop
    async def before_scheduled_tasks(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(SanguineCog(bot))
