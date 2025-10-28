import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import asyncio
import re
from discord import ui, ButtonStyle, Member
from discord.ui import View, Button, Modal, TextInput
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone, time as dt_time
from zoneinfo import ZoneInfo
import gspread.exceptions
import math
from pathlib import Path # Import Path for export function
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

# GSheet Config
SANG_SHEET_ID = "1CCpDAJO7Cq581yF_-rz3vx7L_BTettVaKglSvOmvTOE"
SANG_SHEET_TAB_NAME = "SangSignups"
SANG_HISTORY_TAB_NAME = "History"
# --- CHANGED: Added "Blacklist" ---
SANG_SHEET_HEADER = ["Discord_ID", "Discord_Name", "Favorite Roles", "KC", "Has_Scythe", "Proficiency", "Learning Freeze", "Mentor_Request", "Timestamp", "Blacklist"]

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
    # Remove (RSN#1234) or [RSN#1234] tags
    name = re.sub(r'\s*\([^)]*#\d{4}\)', '', name)
    name = re.sub(r'\s*\[[^\]]*#\d{4}\]', '', name)
    # Remove leading @ from names
    name = re.sub(r'^@', '', name)
    return name.strip()

def normalize_role(p: dict) -> str:
    """Standardizes a player's proficiency based on their sheet data."""
    prof = str(p.get("proficiency","")).strip().lower()
    if prof == "mentor":
        return "mentor"
    try:
        kc = int(p.get("kc") or p.get("KC") or 0)
    except Exception:
        # Fallback for "X" KC or other non-int
        return prof
    if kc <= 10: return "new"
    if 11 <= kc <= 25: return "learner"
    if 26 <= kc <= 100: return "proficient"
    return "highly proficient"

PROF_ORDER = {"mentor": 0, "highly proficient": 1, "proficient": 2, "learner": 3, "new": 4}

def prof_rank(p: dict) -> int:
    """Returns a sortable integer for a player's proficiency."""
    return PROF_ORDER.get(normalize_role(p), 99)

def scythe_icon(p: dict) -> str:
    """Returns a Scythe emoji icon based on player data."""
    return " • <:tob:1272864087105208364>" if p.get("has_scythe") else ""

def freeze_icon(p: dict) -> str:
    """Returns a freeze icon if the player wants to learn."""
    return " • ❄️" if p.get("learning_freeze") else ""

def is_proficient_plus(p: dict) -> bool:
    """Checks if a player is proficient, highly proficient, or mentor."""
    role = normalize_role(p)
    return role in ("mentor", "highly proficient", "proficient")

def parse_roles(roles_str: str) -> (bool, bool):
    """Parses the 'Favorite Roles' string to check for range/melee knowledge."""
    if not roles_str or roles_str == "N/A":
        return False, False
    roles_str = roles_str.lower()
    knows_range = any(s in roles_str for s in ["range", "ranger", "rdps"])
    knows_melee = any(s in roles_str for s in ["melee", "mdps", "meleer"])
    return knows_range, knows_melee

# --- Blacklist helper function ---
def is_blacklist_violation(player: Dict[str, Any], team: List[Dict[str, Any]]) -> bool:
    """Checks if a player joining a team violates any blacklists."""
    player_blacklist = player.get("blacklist", set())
    player_id_str = str(player.get("user_id"))

    for p_in_team in team:
        p_in_team_id_str = str(p_in_team.get("user_id"))

        # Check 1: Does the player on the team (e.g., a mentor) exist in the new player's blacklist?
        if p_in_team_id_str in player_blacklist:
            return True # Player blacklists someone on team

        # Check 2: Does the new player (e.g., a mentor) exist in the team member's blacklist?
        p_in_team_blacklist = p_in_team.get("blacklist", set())
        if player_id_str in p_in_team_blacklist:
            return True # Someone on team blacklists player

    return False

def matchmaking_algorithm(available_raiders: List[Dict[str, Any]]):
    """
    Core algorithm for sorting players into teams.
    """

    # ---------- Sort and segment ----------
    available_raiders.sort(
        key=lambda p: (prof_rank(p), not p.get("has_scythe"), -int(p.get("kc", 0)))
    )

    mentors = [p for p in available_raiders if normalize_role(p) == "mentor"]
    non_mentors = [p for p in available_raiders if normalize_role(p) != "mentor"]

    strong_pool = [p for p in non_mentors if prof_rank(p) <= PROF_ORDER["proficient"]]   # HP/Pro
    learners    = [p for p in non_mentors if normalize_role(p) == "learner"]
    news        = [p for p in non_mentors if normalize_role(p) == "new"]

    mentees = [p for p in non_mentors if p.get("wants_mentor")]
    mentee_ids = {m["user_id"] for m in mentees}
    def _without_mentees(pool): return [p for p in pool if p["user_id"] not in mentee_ids]
    strong_pool = _without_mentees(strong_pool)
    learners    = _without_mentees(learners)
    news        = _without_mentees(news)

    # ---------- Decide target team sizes (only 4/5; 3 only for N in {6,7,11}) ----------
    N = len(available_raiders)
    if N == 0:
        return [], []

    def split_into_4_5(n: int):
        for b in range(n // 5, -1, -1):
            rem = n - 5*b
            if rem % 4 == 0:
                a = rem // 4
                return [5]*b + [4]*a
        return None

    sizes = split_into_4_5(N)
    if sizes is None:
        if N == 6: sizes = [3,3]
        elif N == 7: sizes = [4,3]
        elif N == 11: sizes = [4,4,3]
        else:
            q, r = divmod(N, 4)
            sizes = [4]*q + ([3] if r == 3 else ([] if r == 0 else [4])) # Fallback logic

    T = len(sizes) # Total number of teams

    # ---------- Build anchors (Mentors first, then strongest HP/Pro) ----------
    anchors: List[Optional[Dict[str, Any]]] = [None] * T
    teams: List[List[Dict[str, Any]]] = []

    anchor_pools_normal = [mentors, strong_pool, learners, news, mentees]
    anchor_pools_trio = [strong_pool, learners, news, mentees] # Mentors CANNOT anchor trios
    extra_mentors = []

    for i in range(T):
        target_size = sizes[i]
        pools_to_use = anchor_pools_trio if target_size == 3 else anchor_pools_normal
        anchor = None
        for pool in pools_to_use:
            if pool:
                anchor = pool.pop(0)
                break

        if anchor:
            teams.append([anchor])
        else:
            teams.append([]) # Should only happen if total signups < num teams

    extra_mentors = mentors # Keep track of un-anchored mentors

    # ---------- Helper for safe placement ----------
    def can_add(player, team, max_size) -> bool:
        """Checks if a player can be added to a team based on constraints."""
        if len(team) >= max_size:
            return False

        # Blacklist Check
        if is_blacklist_violation(player, team):
            return False

        future_size = len(team) + 1

        # Trio Rules
        if max_size == 3:
            if normalize_role(player) == "mentor": return False # No mentors in trios
            if not is_proficient_plus(player): return False # Trio must be Proficient+
            if not all(is_proficient_plus(p) for p in team): return False # Current team must be Proficient+

        # Freeze Rule
        if player.get('learning_freeze') and any(p.get('learning_freeze') for p in team):
            return False # Max one freeze learner per team

        # Mentor Rule (Hard Constraint)
        needs_mentor = normalize_role(player) == "new" or player.get("wants_mentor")
        team_has_mentor = any(normalize_role(p) == "mentor" for p in team)
        if needs_mentor and not team_has_mentor:
             return False # New players/Mentees MUST have a mentor

        # Scythe Rule (Activated)
        if future_size == 5:
            # Count how many "New" players would be on the team
            team_new_count = sum(1 for p in team if normalize_role(p) == "new")
            player_is_new = normalize_role(player) == "new"
            total_new = team_new_count + player_is_new

            if total_new == 2: # Team will have exactly two New players
                # Count how many Scythes would be on the team
                team_scythe_count = sum(1 for p in team if p.get("has_scythe"))
                player_has_scythe = player.get("has_scythe")
                total_scythes = team_scythe_count + player_has_scythe

                if total_scythes < 2:
                    return False # BLOCK: Team needs at least 2 scythes for 2 New players

        return True

    max_sizes = list(sizes)

    # ---------- Place Mentees onto Mentor teams first ----------
    mentor_idxs = [i for i, t in enumerate(teams) if any(normalize_role(p) == "mentor" for p in t)] # Use any in case mentor wasn't anchor
    mentees.sort(key=lambda p: (prof_rank(p), not p.get("has_scythe"), -int(p.get("kc", 0))))

    placed_mentees = []
    remaining_mentees = []
    for mentee in mentees:
        placed = False
        for i in mentor_idxs:
            if can_add(mentee, teams[i], max_sizes[i]):
                teams[i].append(mentee)
                placed = True
                placed_mentees.append(mentee)
                break
        if not placed:
            remaining_mentees.append(mentee)
    mentees = remaining_mentees # Mentees who couldn't fit on mentor teams yet

    # ---------- Distribute leftovers (Strong -> Learners -> News -> Mentees -> Extra Mentors) ----------
    leftovers = strong_pool + learners + news + mentees + extra_mentors
    forward = True # Zigzag placement direction
    safety = 0
    MAX_ITER = N * T + 100 # Set a reasonable max iteration count

    while leftovers and safety < MAX_ITER:
        safety += 1
        placed_this_round = False
        idxs_to_try = list(range(T)) if forward else list(range(T-1, -1, -1))
        forward = not forward # Switch direction for next round

        player_to_place = leftovers[0] # Try to place the first player

        placed_player = False
        for i in idxs_to_try:
            if can_add(player_to_place, teams[i], max_sizes[i]):
                teams[i].append(player_to_place)
                leftovers.pop(0) # Remove player from leftovers
                placed_player = True
                placed_this_round = True
                break # Move to the next player

        if not placed_player:
            # Could not place this player in this direction, move to end of queue
            leftovers.append(leftovers.pop(0))

        # Check if stuck (no placements in a full cycle)
        if safety > T * 2 and not placed_this_round and leftovers:
             print(f"Matchmaking potentially stuck. Leftovers: {[p['user_name'] for p in leftovers]}")
             # Advanced recovery / fallback could go here, but for now we break
             break # Avoid infinite loop

    # --- Phase 4: Resolve Stranded Players (SWAP LOGIC) ---
    final_stranded = []
    unplaced = list(leftovers) # Players couldn't fit in the main loop
    leftovers = [] # Reset for this phase

    for player in unplaced:
        is_new_or_mentee = normalize_role(player) == "new" or player.get("wants_mentor")

        # --- Try direct placement first ---
        placed_directly = False
        for i in range(T):
            # If New/Mentee, only try mentor teams. Otherwise, try any team.
            is_mentor_team = any(normalize_role(p) == "mentor" for p in teams[i])
            if is_new_or_mentee and not is_mentor_team:
                continue

            if can_add(player, teams[i], max_sizes[i]):
                 teams[i].append(player)
                 placed_directly = True
                 break
        if placed_directly:
            continue # Successfully placed

        # --- If New/Mentee and couldn't place directly, try swapping with a Learner ---
        if is_new_or_mentee:
            swapped = False
            for i in range(T): # Iterate through potential Mentor teams
                is_mentor_team = any(normalize_role(p) == "mentor" for p in teams[i])
                if not is_mentor_team: continue

                # Find a Learner on this Mentor team to potentially swap out
                learner_to_swap = None
                for p_in_team in teams[i]:
                    if normalize_role(p_in_team) == "learner":
                        # Check if swapping this learner out violates the New player's blacklist
                        temp_mentor_team_after_swap = [p for p in teams[i] if p != p_in_team] + [player]
                        if not is_blacklist_violation(player, temp_mentor_team_after_swap):
                             learner_to_swap = p_in_team
                             break # Found a potential learner to swap

                if learner_to_swap:
                    # Found a Learner! Now find a new home for this Learner
                    new_home_for_learner_idx = -1
                    for j in range(T):
                        if i == j: continue # Don't swap onto the same team
                        # Learner can go to non-mentor team, check size & blacklist
                        if len(teams[j]) < max_sizes[j] and not is_blacklist_violation(learner_to_swap, teams[j]):
                            new_home_for_learner_idx = j
                            break

                    if new_home_for_learner_idx != -1:
                        # Swap is possible!
                        teams[i].remove(learner_to_swap)
                        teams[i].append(player)
                        teams[new_home_for_learner_idx].append(learner_to_swap)
                        swapped = True
                        print(f"Swap executed: {player['user_name']} (New/Mentee) swapped with {learner_to_swap['user_name']} (Learner)")
                        break # Swapped successfully, move to next stranded player

            if swapped:
                continue # Successfully swapped

        # --- If still not placed (Learner, Proficient, HP, or failed New swap), try any team as last resort ---
        placed_last_resort = False
        for i in range(T):
            # We break the mentor rule here if absolutely necessary, but still respect blacklist & size
            if len(teams[i]) < max_sizes[i] and not is_blacklist_violation(player, teams[i]):
                 # Re-check freeze rule just in case
                 if player.get('learning_freeze') and any(p.get('learning_freeze') for p in teams[i]):
                     continue
                 # Re-check scythe rule
                 if max_sizes[i] == 5:
                    future_team = teams[i] + [player]
                    future_new_count = sum(1 for p in future_team if normalize_role(p) == "new")
                    if future_new_count == 2:
                        future_scythe_count = sum(1 for p in future_team if p.get("has_scythe"))
                        if future_scythe_count < 2:
                            continue # Cannot place due to scythe rule

                 teams[i].append(player)
                 placed_last_resort = True
                 print(f"Last Resort Placement: {player['user_name']} placed on Team {i+1}")
                 break

        if not placed_last_resort:
            final_stranded.append(player) # Truly cannot be placed

    # --- Phase 5: Balance "New" Player KC across Mentor Teams ---
    mentor_teams_indices = [i for i, t in enumerate(teams) if any(normalize_role(p) == "mentor" for p in t)]

    if len(mentor_teams_indices) > 1:
        def get_team_new_kc(team_idx):
            team = teams[team_idx]
            return sum(int(p.get("kc", 0)) for p in team if normalize_role(p) == "new")

        # Sort teams by the total KC of their "New" players
        mentor_teams_indices.sort(key=get_team_new_kc)

        low_kc_team_idx = mentor_teams_indices[0]
        high_kc_team_idx = mentor_teams_indices[-1]

        low_kc_team = teams[low_kc_team_idx]
        high_kc_team = teams[high_kc_team_idx]

        if get_team_new_kc(high_kc_team_idx) > get_team_new_kc(low_kc_team_idx):
            # Find highest KC "New" player on the high team
            new_from_high = sorted([p for p in high_kc_team if normalize_role(p) == "new"], key=lambda p: -int(p.get("kc", 0)))
            # Find lowest KC "New" player on the low team
            new_from_low = sorted([p for p in low_kc_team if normalize_role(p) == "new"], key=lambda p: int(p.get("kc", 0)))

            if new_from_high and new_from_low:
                player_to_move_up = new_from_high[0] # Highest KC from high team
                player_to_move_down = new_from_low[0] # Lowest KC from low team

                # Only swap if there's a difference in KC
                if int(player_to_move_up.get("kc", 0)) > int(player_to_move_down.get("kc", 0)):
                    # Check blacklists BEFORE swapping
                    temp_low_team_after_swap = [p for p in low_kc_team if p != player_to_move_down] + [player_to_move_up]
                    temp_high_team_after_swap = [p for p in high_kc_team if p != player_to_move_up] + [player_to_move_down]

                    if not is_blacklist_violation(player_to_move_up, temp_low_team_after_swap) and \
                       not is_blacklist_violation(player_to_move_down, temp_high_team_after_swap):
                        # Perform the swap
                        low_kc_team.remove(player_to_move_down)
                        low_kc_team.append(player_to_move_up)
                        high_kc_team.remove(player_to_move_up)
                        high_kc_team.append(player_to_move_down)
                        print(f"Balancing Swap: Moved {player_to_move_up.get('user_name')} to Team {low_kc_team_idx+1}.")
                        print(f"Balancing Swap: Moved {player_to_move_down.get('user_name')} to Team {high_kc_team_idx+1}.")

    return teams, final_stranded

def format_player_line_plain(guild: discord.Guild, p: dict) -> str:
    """Formats a player's info for the no-ping /sangmatchtest command."""
    nickname = p.get("user_name") or "Unknown"
    role_text = p.get("proficiency", "Unknown").replace(" ", "-").capitalize().replace("-", " ")
    kc_raw = p.get("kc", 0)
    kc_text = f"({kc_raw} KC)" if isinstance(kc_raw, int) and kc_raw > 0 and role_text != "Mentor" and kc_raw != 9999 else ""
    scythe = scythe_icon(p)
    freeze = freeze_icon(p)
    return f"{nickname} • **{role_text}** {kc_text}{scythe}{freeze}"

def format_player_line_mention(guild: discord.Guild, p: dict) -> str:
    """Formats a player's info for the /sangmatch command with pings."""
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
    """Modal form for regular raiders to sign up."""
    roles_known = TextInput(label="Favorite Roles (Leave blank if None)", placeholder="Inputs: All, Nfrz, Sfrz, Mdps, Rdps", style=discord.TextStyle.short, max_length=4, required=False)
    kc = TextInput(label="What is your N͟o͟r͟m͟a͟l͟ Mode ToB KC?", placeholder="0-10 = New, 11-25 = Learner, 26-100 = Proficient, 100+ = Highly Proficient", style=discord.TextStyle.short, max_length=5, required=True)
    has_scythe = TextInput(label="Do you have a Scythe? (Yes/No)", placeholder="Yes or No O͟N͟L͟Y͟", style=discord.TextStyle.short, max_length=3, required=True)
    learning_freeze = TextInput(label="Learn freeze role? (Yes or leave blank)", placeholder="Yes or blank/No O͟N͟L͟Y͟", style=discord.TextStyle.short, max_length=3, required=False)
    wants_mentor = TextInput(label="Do you want assistance from a Mentor?", placeholder="Yes or No/Blank", style=discord.TextStyle.short, max_length=3, required=False)

    def __init__(self, cog: 'SanguineCog', previous_data: dict = None):
        super().__init__(title="Sanguine Sunday Signup")
        self.cog = cog
        if previous_data:
            self.roles_known.default = previous_data.get("Favorite Roles", "")
            kc_val = previous_data.get("KC", "")
            self.kc.default = str(kc_val) if kc_val not in ["", None, "X"] else ""
            self.has_scythe.default = "Yes" if previous_data.get("Has_Scythe", False) else "No"
            self.learning_freeze.default = "Yes" if previous_data.get("Learning Freeze", False) else ""
            self.wants_mentor.default = "Yes" if previous_data.get("Mentor_Request", False) else ""

        self.previous_data = previous_data # Store for blacklist

    async def on_submit(self, interaction: discord.Interaction):
        if not self.cog.sang_sheet:
            await interaction.response.send_message("⚠️ Error: The Sanguine Sunday signup sheet is not connected. Please contact staff.", ephemeral=True)
            return

        try:
            kc_value = int(str(self.kc))
            if kc_value < 0: raise ValueError("KC cannot be negative.")
        except ValueError:
            await interaction.response.send_message("⚠️ Error: Kill Count must be a valid number.", ephemeral=True)
            return

        scythe_value = str(self.has_scythe).strip().lower()
        if scythe_value not in ["yes", "no", "y", "n"]:
            await interaction.response.send_message("⚠️ Error: Scythe must be 'Yes' or 'No'.", ephemeral=True)
            return
        has_scythe_bool = scythe_value in ["yes", "y"]

        proficiency_value = ""
        if kc_value <= 10: proficiency_value = "New"
        elif 11 <= kc_value <= 25: proficiency_value = "Learner"
        elif 26 <= kc_value <= 100: proficiency_value = "Proficient"
        else: proficiency_value = "Highly Proficient"

        roles_known_value = str(self.roles_known).strip() or "None"
        learning_freeze_value = str(self.learning_freeze).strip().lower()
        learning_freeze_bool = learning_freeze_value in ["yes", "y"]
        wants_mentor_value = str(self.wants_mentor).strip().lower()
        wants_mentor_bool = wants_mentor_value in ["yes", "y"]

        user_id = str(interaction.user.id)
        user_name = sanitize_nickname(interaction.user.display_name)
        timestamp = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S")

        # --- Preserve existing blacklist data from History ---
        if not self.previous_data: # Fetch if not provided
            self.previous_data = self.cog.get_previous_signup(user_id)
        blacklist_value = self.previous_data.get("Blacklist", "") if self.previous_data else ""

        row_data = [user_id, user_name, roles_known_value, kc_value, has_scythe_bool, proficiency_value, learning_freeze_bool, wants_mentor_bool, timestamp, blacklist_value]

        try:
            # Update SangSignups sheet
            cell = self.cog.sang_sheet.find(user_id, in_column=1)
            if cell is None:
                self.cog.sang_sheet.append_row(row_data)
                print(f"Appended signup for {user_name}")
            else:
                self.cog.sang_sheet.update(values=[row_data], range_name=f'A{cell.row}:J{cell.row}')
                print(f"Updated signup for {user_name} at row {cell.row}")

            # Update History sheet
            if self.cog.history_sheet:
                try:
                    history_cell = self.cog.history_sheet.find(user_id, in_column=1)
                    if history_cell is None:
                        self.cog.history_sheet.append_row(row_data)
                        print(f"Appended history for {user_name}")
                    else:
                        # Only update history if new data is different (except timestamp)
                        old_data = self.cog.history_sheet.row_values(history_cell.row)
                        # Compare relevant fields (cols 3 to 8 and 10)
                        if old_data[2:8] != row_data[2:8] or old_data[9] != row_data[9]:
                             self.cog.history_sheet.update(values=[row_data], range_name=f'A{history_cell.row}:J{history_cell.row}')
                             print(f"Updated history for {user_name} at row {history_cell.row}")

                except gspread.exceptions.CellNotFound: # Handle if user not in history yet
                    self.cog.history_sheet.append_row(row_data)
                    print(f"Appended history (not found) for {user_name}")
                except Exception as e:
                    print(f"🔥 GSpread error on HISTORY (User Form) write: {e}")
            else:
                print("🔥 History sheet not available, skipping history append.")

        except Exception as e:
            print(f"🔥 GSpread error on signup: {e}")
            await interaction.response.send_message("⚠️ An error occurred while saving your signup.", ephemeral=True)
            return

        await interaction.response.send_message(
            f"✅ **You are signed up as {proficiency_value}!**\n"
            f"**KC:** {kc_value}\n"
            f"**Scythe:** {'Yes' if has_scythe_bool else 'No'}\n"
            f"**Favorite Roles:** {roles_known_value}\n"
            f"**Learn Freeze:** {'Yes' if learning_freeze_bool else 'No'}\n"
            f"**Mentor Request:** {'Yes' if wants_mentor_bool else 'No'}",
            ephemeral=True
        )


class MentorSignupForm(Modal, title="Sanguine Sunday Mentor Signup"):
    """Modal form for Mentors to sign up."""
    roles_known = TextInput(label="Favorite Roles (Leave blank if None)", placeholder="Inputs: All, Nfrz, Sfrz, Mdps, Rdps", style=discord.TextStyle.short, max_length=4, required=True)
    kc = TextInput(label="What is your N͟o͟r͟m͟a͟l͟ Mode ToB KC?", placeholder="150+", style=discord.TextStyle.short, max_length=5, required=True)
    has_scythe = TextInput(label="Do you have a Scythe? (Yes/No)", placeholder="Yes or No", style=discord.TextStyle.short, max_length=3, required=True)

    def __init__(self, cog: 'SanguineCog', previous_data: dict = None):
        super().__init__(title="Sanguine Sunday Mentor Signup")
        self.cog = cog
        if previous_data:
             self.roles_known.default = previous_data.get("Favorite Roles", "")
             kc_val = previous_data.get("KC", "")
             self.kc.default = str(kc_val) if kc_val not in ["", None, "X"] else ""
             self.has_scythe.default = "Yes" if previous_data.get("Has_Scythe", False) else "No"

        self.previous_data = previous_data # Store for blacklist

    async def on_submit(self, interaction: discord.Interaction):
        if not self.cog.sang_sheet:
            await interaction.response.send_message("⚠️ Error: The Sanguine Sunday signup sheet is not connected.", ephemeral=True)
            return

        try:
            kc_value = int(str(self.kc))
            if kc_value < 50:
                await interaction.response.send_message("⚠️ Mentors should have 50+ KC to sign up via form.", ephemeral=True)
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
        user_name = sanitize_nickname(interaction.user.display_name)
        timestamp = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S")

        # --- Preserve existing blacklist data from History ---
        if not self.previous_data: # Fetch if not provided
            self.previous_data = self.cog.get_previous_signup(user_id)
        blacklist_value = self.previous_data.get("Blacklist", "") if self.previous_data else ""

        row_data = [user_id, user_name, roles_known_value, kc_value, has_scythe_bool, proficiency_value, learning_freeze_bool, False, timestamp, blacklist_value]

        try:
            # Update SangSignups sheet
            cell = self.cog.sang_sheet.find(user_id, in_column=1)
            if cell is None:
                self.cog.sang_sheet.append_row(row_data)
                print(f"Appended mentor signup for {user_name}")
            else:
                self.cog.sang_sheet.update(values=[row_data], range_name=f'A{cell.row}:J{cell.row}')
                print(f"Updated mentor signup for {user_name} at row {cell.row}")

            # Update History sheet
            if self.cog.history_sheet:
                try:
                    history_cell = self.cog.history_sheet.find(user_id, in_column=1)
                    if history_cell is None:
                        self.cog.history_sheet.append_row(row_data)
                        print(f"Appended mentor history for {user_name}")
                    else:
                        # Only update history if relevant data changed
                        old_data = self.cog.history_sheet.row_values(history_cell.row)
                        if old_data[2:8] != row_data[2:8] or old_data[9] != row_data[9]:
                            self.cog.history_sheet.update(values=[row_data], range_name=f'A{history_cell.row}:J{history_cell.row}')
                            print(f"Updated mentor history for {user_name} at row {history_cell.row}")

                except gspread.exceptions.CellNotFound:
                    self.cog.history_sheet.append_row(row_data)
                    print(f"Appended mentor history (not found) for {user_name}")
                except Exception as e:
                    print(f"🔥 GSpread error on HISTORY (Mentor Form) write: {e}")
            else:
                print("🔥 History sheet not available, skipping history append.")

        except Exception as e:
            print(f"🔥 GSpread error on mentor signup: {e}")
            await interaction.response.send_message("⚠️ An error occurred while saving your signup.", ephemeral=True)
            return

        await interaction.response.send_message(
            f"✅ **You are signed up as a Mentor!**\n"
            f"**KC:** {kc_value}\n"
            f"**Scythe:** {'Yes' if has_scythe_bool else 'No'}\n"
            f"**Favorite Roles:** {roles_known_value}",
            ephemeral=True
        )


class WithdrawalButton(ui.Button):
    """A simple button to withdraw from the event."""
    def __init__(self, cog: 'SanguineCog'):
        super().__init__(label="Withdraw", style=ButtonStyle.secondary, custom_id="sang_withdraw", emoji="❌")
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_name = interaction.user.display_name

        if not self.cog.sang_sheet:
            await interaction.response.send_message("⚠️ Error: The Sanguine Signup sheet is not connected.", ephemeral=True)
            return

        try:
            cell = self.cog.sang_sheet.find(user_id, in_column=1)
            if cell is None:
                await interaction.response.send_message(f"ℹ️ {user_name}, you are not currently signed up for this week's event.", ephemeral=True)
                return

            self.cog.sang_sheet.delete_rows(cell.row)
            await interaction.response.send_message(f"✅ **{user_name}**, you have been successfully withdrawn from this week's Sanguine Sunday signups.", ephemeral=True)
            print(f"✅ User {user_id} ({user_name}) withdrew from SangSignups.")
        except Exception as e:
            print(f"🔥 GSpread error on withdrawal: {e}")
            await interaction.response.send_message("⚠️ An error occurred while processing your withdrawal.", ephemeral=True)

class SignupView(View):
    """The persistent view with the 3 main buttons: Raider, Mentor, Withdraw."""
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

        has_mentor_role = any(role.id == MENTOR_ROLE_ID for role in member.roles)
        previous_data = self.cog.get_previous_signup(str(user.id))

        # If user has Mentor role, try auto-signup first
        if has_mentor_role:
            await interaction.response.defer(ephemeral=True)
            if not self.cog.sang_sheet or not self.cog.history_sheet:
                await interaction.followup.send("⚠️ Error: Sheets not connected.", ephemeral=True)
                return

            user_id = str(user.id)
            user_name = member.display_name
            timestamp = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S")

            # Preserve blacklist
            blacklist_value = previous_data.get("Blacklist", "") if previous_data else ""
            row_data = [user_id, user_name, "All", "X", True, "Mentor", False, False, timestamp, blacklist_value]

            try:
                # Update SangSignups
                cell = self.cog.sang_sheet.find(user_id, in_column=1)
                if cell is None: self.cog.sang_sheet.append_row(row_data)
                else: self.cog.sang_sheet.update(values=[row_data], range_name=f'A{cell.row}:J{cell.row}')

                # Update History
                if self.cog.history_sheet:
                    try:
                        history_cell = self.cog.history_sheet.find(user_id, in_column=1)
                        if history_cell is None: self.cog.history_sheet.append_row(row_data)
                        else:
                            # Only update history if relevant data changed
                            old_data = self.cog.history_sheet.row_values(history_cell.row)
                            if old_data[2:8] != row_data[2:8] or old_data[9] != row_data[9]:
                                self.cog.history_sheet.update(values=[row_data], range_name=f'A{history_cell.row}:J{history_cell.row}')
                    except gspread.exceptions.CellNotFound:
                        self.cog.history_sheet.append_row(row_data)
                    except Exception as e: print(f"🔥 GSpread history error (Auto-Mentor): {e}")
                else: print("🔥 History sheet unavailable.")

                await interaction.followup.send("✅ **Auto-signed up as Mentor!**\nTo edit details, click 'Mentor' again to open the form.", ephemeral=True)
            except Exception as e:
                print(f"🔥 GSpread error on auto mentor signup: {e}")
                await interaction.followup.send("⚠️ Error during auto-signup.", ephemeral=True)
        else:
             # If no mentor role, always show the form
            await interaction.response.send_modal(MentorSignupForm(self.cog, previous_data=previous_data))


# ---------------------------
# 🔹 Sanguine Cog Class
# ---------------------------

class SanguineCog(commands.Cog):
    """
    This class holds all the commands, listeners, and tasks
    for the Sanguine Sunday event.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sang_sheet = None
        self.history_sheet = None

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
                    print(f"⚠️ Sanguine sheet header mismatch. Expected: {SANG_SHEET_HEADER}, Found: {header}. Re-writing...")
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
                    print(f"⚠️ Sanguine history sheet header mismatch. Expected: {SANG_SHEET_HEADER}, Found: {header}. Re-writing...")
                    self.history_sheet.clear()
                    self.history_sheet.append_row(SANG_SHEET_HEADER)
            except gspread.exceptions.WorksheetNotFound:
                print(f"'{SANG_HISTORY_TAB_NAME}' not found. Creating...")
                self.history_sheet = sang_google_sheet.add_worksheet(title=SANG_HISTORY_TAB_NAME, rows="1000", cols="20")
                self.history_sheet.append_row(SANG_SHEET_HEADER)

            print("✅ Sanguine Cog: Google Sheets initialized successfully.")
        except Exception as e:
            print(f"🔥 CRITICAL ERROR initializing SanguineCog GSheets: {e}")

        # Add the persistent view AFTER GSheets are potentially initialized
        self.bot.add_view(SignupView(self))

    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the cog is loaded and the bot is ready."""
        # Ensure GSheets are available before starting tasks
        if not self.sang_sheet or not self.history_sheet:
             print("🔥 Sanguine Cog: GSheets failed to initialize. Scheduled tasks will not start.")
             return

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

    # --- Cog Methods (from helper functions) ---

    async def _create_team_embeds(self, teams, title, description, color, guild, format_func):
        """Helper function to build and paginate team embeds."""
        embeds = []
        if not teams:
            return embeds

        current_embed = discord.Embed(title=title, description=description, color=color)
        embeds.append(current_embed)
        field_count = 0

        FIELDS_PER_EMBED = 10 # Keep this relatively low

        for i, team in enumerate(teams, start=1):
            if field_count >= FIELDS_PER_EMBED:
                # Start new embed if current one is full
                current_embed = discord.Embed(title=f"{title} (Page {len(embeds) + 1})", color=color)
                embeds.append(current_embed)
                field_count = 0

            # Sort players within the team for display
            team_sorted = sorted(team, key=prof_rank)
            lines = [format_func(guild, p) for p in team_sorted]

            # Add the team as a field to the current embed
            current_embed.add_field(
                name=f"Team {i} (Size: {len(team)})",
                value="\n".join(lines) if lines else "—",
                inline=False
            )
            field_count += 1

        return embeds

    def get_previous_signup(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetches the latest signup data for a user from the HISTORY sheet."""
        if not self.history_sheet:
            print("History sheet not available in get_previous_signup.")
            return None
        try:
            # Fetch all records. Consider caching or more targeted fetch if performance is an issue.
            all_records = self.history_sheet.get_all_records()
            if not all_records:
                 print("No records found in history_sheet.")
                 return None

            # Iterate backwards to find the most recent entry for the user
            for record in reversed(all_records):
                sheet_discord_id = record.get("Discord_ID")
                # Ensure comparison is done with strings
                sheet_discord_id_str = str(sheet_discord_id) if sheet_discord_id is not None else None

                if sheet_discord_id_str == user_id:
                    # Convert boolean-like strings to actual booleans
                    record["Has_Scythe"] = str(record.get("Has_Scythe", "FALSE")).strip().upper() == "TRUE"
                    record["Learning Freeze"] = str(record.get("Learning Freeze", "FALSE")).strip().upper() == "TRUE"
                    record["Mentor_Request"] = str(record.get("Mentor_Request", "FALSE")).strip().upper() == "TRUE"
                    # Blacklist is read directly as a string
                    return record # Return the found record

            print(f"No history match found for user_id: {user_id}")
            return None
        except Exception as e:
            print(f"🔥 GSpread error fetching previous signup for {user_id}: {e}")
            return None

    async def post_signup(self, channel: discord.TextChannel):
        """Posts the main signup message with the signup buttons."""
        # Optional: Delete previous signup message if desired
        # async for message in channel.history(limit=10):
        #     if message.author == self.bot.user and SANG_MESSAGE_IDENTIFIER in message.content:
        #         await message.delete()
        #         break
        await channel.send(SANG_MESSAGE, view=SignupView(self))
        print(f"✅ Posted Sanguine Sunday signup in #{channel.name}")

    async def post_reminder(self, channel: discord.TextChannel):
        """Finds learners and posts a reminder."""
        if not self.sang_sheet:
            print("⚠️ Cannot post reminder, Sang Sheet not connected.")
            return False

        # Clean up old reminders
        try:
            async for message in channel.history(limit=50):
                if message.author == self.bot.user and LEARNER_REMINDER_IDENTIFIER in message.content:
                    await message.delete()
        except discord.Forbidden:
            print(f"⚠️ Could not delete old reminders in #{channel.name}")
        except Exception as e:
            print(f"🔥 Error cleaning up reminders: {e}")

        learners_to_ping = []
        try:
            all_signups = self.sang_sheet.get_all_records()
            for signup in all_signups:
                proficiency = str(signup.get("Proficiency", "")).lower()
                # Ping "New" and "Learner" players
                if proficiency in ["learner", "new"]:
                    user_id = signup.get('Discord_ID')
                    if user_id:
                        # Ensure user ID is valid before adding
                        try:
                            learners_to_ping.append(f"<@{int(user_id)}>")
                        except ValueError:
                            print(f"⚠️ Invalid Discord ID found in sheet: {user_id}")

            if not learners_to_ping:
                reminder_content = f"{LEARNER_REMINDER_MESSAGE}\n\n_No learners have signed up yet._"
            else:
                learner_pings_str = " ".join(learners_to_ping)
                reminder_content = f"{LEARNER_REMINDER_MESSAGE}\n\n**Learners:** {learner_pings_str}"

            # Post the new reminder
            await channel.send(reminder_content, allowed_mentions=discord.AllowedMentions(users=True))
            print(f"✅ Posted Sanguine Sunday learner reminder in #{channel.name}")
            return True
        except Exception as e:
            print(f"🔥 GSpread error fetching/posting reminder: {e}")
            # Send error message to the channel
            await channel.send("⚠️ Error processing learner list from the signup sheet.")
            return False


    # --- Slash Commands ---

    @app_commands.command(name="sangsignup", description="Manage Sanguine Sunday signups.")
    @app_commands.checks.has_role(STAFF_ROLE_ID)
    @app_commands.describe(variant="Choose the action to perform.", channel="Optional channel to post in (defaults to the configured event channel).")
    @app_commands.choices(variant=[
        app_commands.Choice(name="Post Signup Message", value=1),
        app_commands.Choice(name="Post Learner Reminder", value=2),
    ])
    async def sangsignup(self, interaction: discord.Interaction, variant: int, channel: Optional[discord.TextChannel] = None):
        target_channel = channel or self.bot.get_channel(SANG_POST_CHANNEL_ID) # Use specific post channel ID
        if not target_channel:
            await interaction.response.send_message("⚠️ Could not find the target channel.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        if variant == 1:
            await self.post_signup(target_channel)
            await interaction.followup.send(f"✅ Signup message posted in {target_channel.mention}.")
        elif variant == 2:
            result = await self.post_reminder(target_channel)
            if result:
                await interaction.followup.send(f"✅ Learner reminder posted in {target_channel.mention}.")
            else:
                await interaction.followup.send("⚠️ Could not post the reminder.")

    @app_commands.command(name="sangmatch", description="Create ToB teams from signups in a voice channel.")
    @app_commands.checks.has_role(STAFF_ROLE_ID)
    @app_commands.describe(voice_channel="Optional: The voice channel to pull users from. If omitted, uses all signups.")
    async def sangmatch(self, interaction: discord.Interaction, voice_channel: Optional[discord.VoiceChannel] = None):
        if not self.sang_sheet:
            await interaction.response.send_message("⚠️ Error: The Sanguine Sunday sheet is not connected.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=False) # Public response

        vc_member_ids = None
        channel_name = "All Signups"
        if voice_channel:
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
            # Filter out header row if present
            if all_signups_records and all_signups_records[0].get("Discord_ID") == "Discord_ID":
                all_signups_records = all_signups_records[1:]
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
            # Skip if filtering by VC and user not in VC
            if vc_member_ids and user_id not in vc_member_ids:
                 continue

            roles_str = signup.get("Favorite Roles", "")
            knows_range, knows_melee = parse_roles(roles_str)
            kc_raw = signup.get("KC", 0)

            # Handle potential 'X' KC for mentors or invalid data
            try:
                kc_val = int(kc_raw)
            except (ValueError, TypeError):
                # Assign high KC for sorting if mentor, 0 otherwise
                kc_val = 9999 if str(signup.get("Proficiency", "")).lower() == 'mentor' else 0

            proficiency_val = str(signup.get("Proficiency", "")).lower()

            # Re-calculate proficiency based on KC unless already Mentor
            if proficiency_val != 'mentor':
                if kc_val <= 10: proficiency_val = "new"
                elif 11 <= kc_val <= 25: proficiency_val = "learner"
                elif 26 <= kc_val <= 100: proficiency_val = "proficient"
                else: proficiency_val = "highly proficient"

            # Process Blacklist
            blacklist_str = str(signup.get("Blacklist", ""))
            blacklist_ids = set(bid.strip() for bid in blacklist_str.split(',') if bid.strip())

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
                "blacklist": blacklist_ids # Pass blacklist set to algorithm
            })

        if not available_raiders:
            await interaction.followup.send(f"⚠️ None of the users in {voice_channel.mention} have signed up for the event." if voice_channel else "⚠️ No eligible signups found.")
            return

        # --- Run the matchmaking ---
        teams, stranded_players = matchmaking_algorithm(available_raiders)

        guild = interaction.guild
        category = guild.get_channel(SANG_VC_CATEGORY_ID)

        # Create Voice Channels
        if category and isinstance(category, discord.CategoryChannel):
            for i in range(len(teams)):
                try:
                    # Check if channel already exists to avoid duplicates
                    vc_name = f"SanguineSunday – Team {i+1}"
                    existing_channel = discord.utils.get(category.voice_channels, name=vc_name)
                    if not existing_channel:
                         await category.create_voice_channel(name=vc_name, user_limit=5)
                except discord.Forbidden:
                    print(f"Error creating VC: Missing permissions.")
                    await interaction.followup.send("⚠️ I don't have permissions to create voice channels.", ephemeral=True)
                    break # Stop trying if permissions fail once
                except Exception as e:
                    print(f"Error creating VC: {e}")
        else:
             print("⚠️ VC Category not found or is not a category channel.")

        post_channel = interaction.channel # Post in the channel where command was used

        # Prepare Embeds
        embed_title = f"Sanguine Sunday Teams - {channel_name}"
        embed_desc = f"Created {len(teams)} valid team(s) from {len(available_raiders)} available signed-up users."

        team_embeds = await self._create_team_embeds(
            teams,
            embed_title,
            embed_desc,
            discord.Color.red(),
            guild,
            format_player_line_mention # Use function with pings
        )

        global last_generated_teams # Update global cache
        last_generated_teams = teams

        # Send Embeds
        initial_message = None
        for i, embed in enumerate(team_embeds):
            if i == 0:
                initial_message = await interaction.followup.send(embed=embed, wait=True) # Send first embed as followup
            else:
                await post_channel.send(embed=embed) # Send subsequent embeds normally

        # Handle Stranded Players (if any) - Should ideally not happen with swap logic
        if stranded_players:
             stranded_names = [format_player_line_plain(guild, p) for p in stranded_players]
             stranded_text = "\n".join(stranded_names)
             warning_embed = discord.Embed(
                  title="⚠️ Stranded Players",
                  description=f"The following players could not be placed due to team constraints or blacklists:\n{stranded_text}",
                  color=discord.Color.orange()
             )
             # Send stranded list publicly after teams
             await post_channel.send(embed=warning_embed)


    @app_commands.command(name="sangmatchtest", description="Create ToB teams without pinging or creating voice channels; show plain-text nicknames.")
    @app_commands.checks.has_role(STAFF_ROLE_ID)
    @app_commands.describe(voice_channel="Optional: The voice channel to pull users from. If omitted, uses all signups.", channel="(Optional) Override the text channel to post teams (testing).")
    async def sangmatchtest(self, interaction: discord.Interaction, voice_channel: Optional[discord.VoiceChannel] = None, channel: Optional[discord.TextChannel] = None):
        if not self.sang_sheet:
            await interaction.response.send_message("⚠️ Error: The Sanguine Sunday sheet is not connected.", ephemeral=True)
            return
        # Use ephemeral=True for test command response
        await interaction.response.defer(ephemeral=True)

        vc_member_ids = None
        channel_name = "All Signups"
        if voice_channel:
            channel_name = voice_channel.name
            if not voice_channel.members:
                await interaction.followup.send(f"⚠️ No users are in {voice_channel.mention}.", ephemeral=True)
                return
            vc_member_ids = {str(m.id) for m in voice_channel.members if not m.bot}
            if not vc_member_ids:
                await interaction.followup.send(f"⚠️ No human users are in {voice_channel.mention}.", ephemeral=True)
                return

        try:
            all_signups_records = self.sang_sheet.get_all_records()
            # Filter header
            if all_signups_records and all_signups_records[0].get("Discord_ID") == "Discord_ID":
                all_signups_records = all_signups_records[1:]
        except Exception as e:
            await interaction.followup.send("⚠️ An error occurred fetching signups from the database.", ephemeral=True)
            return

        available_raiders = []
        for signup in all_signups_records:
            user_id = str(signup.get("Discord_ID"))
            if vc_member_ids and user_id not in vc_member_ids: continue

            roles_str = signup.get("Favorite Roles", "")
            knows_range, knows_melee = parse_roles(roles_str)
            kc_raw = signup.get("KC", 0)
            try: kc_val = int(kc_raw)
            except (ValueError, TypeError): kc_val = 9999 if str(signup.get("Proficiency", "")).lower() == 'mentor' else 0

            proficiency_val = str(signup.get("Proficiency", "")).lower()
            if proficiency_val != 'mentor':
                if kc_val <= 10: proficiency_val = "new"
                elif 11 <= kc_val <= 25: proficiency_val = "learner"
                elif 26 <= kc_val <= 100: proficiency_val = "proficient"
                else: proficiency_val = "highly proficient"

            blacklist_str = str(signup.get("Blacklist", ""))
            blacklist_ids = set(bid.strip() for bid in blacklist_str.split(',') if bid.strip())

            available_raiders.append({
                "user_id": user_id, "user_name": sanitize_nickname(signup.get("Discord_Name")),
                "proficiency": proficiency_val, "kc": kc_val,
                "has_scythe": str(signup.get("Has_Scythe", "FALSE")).upper() == "TRUE",
                "roles_known": roles_str, "learning_freeze": str(signup.get("Learning Freeze", "FALSE")).upper() == "TRUE",
                "knows_range": knows_range, "knows_melee": knows_melee,
                "wants_mentor": str(signup.get("Mentor_Request", "FALSE")).upper() == "TRUE",
                "blacklist": blacklist_ids
            })

        if not available_raiders:
            await interaction.followup.send("⚠️ No eligible signups found.", ephemeral=True)
            return

        # --- Run matchmaking ---
        teams, stranded_players = matchmaking_algorithm(available_raiders)

        guild = interaction.guild
        # Use specified channel or current channel for test output
        post_channel = channel or interaction.channel

        embed_title = f"Sanguine Sunday Teams (Test, no pings/VC) - {channel_name}"
        embed_desc = f"Created {len(teams)} valid team(s) from {len(available_raiders)} available signed-up users."

        team_embeds = await self._create_team_embeds(
            teams,
            embed_title,
            embed_desc,
            discord.Color.dark_gray(),
            guild,
            format_player_line_plain # Use function WITHOUT pings
        )

        global last_generated_teams # Update cache even for test runs
        last_generated_teams = teams

        # Send embeds (ephemerally if possible, or to target channel)
        try:
            # Try sending first embed ephemerally
            await interaction.followup.send(embed=team_embeds[0], ephemeral=True)
            # Send remaining embeds publicly to the target channel
            for embed in team_embeds[1:]:
                await post_channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        except discord.HTTPException:
             # If ephemeral fails (e.g., too large), send all publicly
             await interaction.followup.send("Embed too large for ephemeral message, posting publicly.", ephemeral=True)
             for embed in team_embeds:
                 await post_channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())

        # Report stranded players ephemerally
        if stranded_players:
             stranded_names = [format_player_line_plain(guild, p) for p in stranded_players]
             stranded_text = "\n".join(stranded_names)
             await interaction.followup.send(f"⚠️ **Stranded Players:**\n{stranded_text}", ephemeral=True)


    @app_commands.command(name="sangexport", description="Export the most recently generated teams to a text file.")
    @app_commands.checks.has_any_role("Administrators", "Clan Staff", "Senior Staff", "Staff", "Trial Staff")
    async def sangexport(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        global last_generated_teams
        teams = last_generated_teams
        if not teams:
            await interaction.followup.send("⚠️ No teams found from the last matchmaking run in this session.", ephemeral=True)
            return

        guild = interaction.guild
        lines = []
        for i, team in enumerate(teams, start=1):
            lines.append(f"Team {i} (Size: {len(team)})")
            # Sort team members for export consistency
            team_sorted = sorted(team, key=prof_rank)
            for p in team_sorted:
                sname = sanitize_nickname(p.get("user_name", "Unknown"))
                mid = p.get("user_id")
                id_text = str(mid) if mid is not None else "UnknownID"
                prof = p.get("proficiency", "Unknown").capitalize()
                kc = p.get("kc", "-")
                kc_str = f"({kc} KC)" if kc != 9999 and kc != "-" and prof != "Mentor" else ""
                lines.append(f"  - {sname} [{prof} {kc_str}] — ID: {id_text}")
            lines.append("") # Blank line between teams
        txt = "\n".join(lines)

        # Define export path
        export_dir = Path(os.getenv("SANG_EXPORT_DIR", "/tmp/sang_exports")) # Use /tmp as a safer default
        try:
            export_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error creating export directory {export_dir}: {e}")
            await interaction.followup.send(f"⚠️ Could not create export directory.", ephemeral=True)
            return

        ts = datetime.now(CST).strftime("%Y%m%d_%H%M%S")
        outpath = export_dir / f"sanguine_teams_{ts}.txt"

        try:
            # Write to file
            with open(outpath, "w", encoding="utf-8") as f:
                f.write(txt)

            # Send file to user
            await interaction.followup.send(content=f"📄 Exported {len(teams)} teams.", file=discord.File(str(outpath), filename=outpath.name), ephemeral=True)
            print(f"Exported teams to {outpath}")
        except Exception as e:
            print(f"🔥 Failed to write or send export file: {e}")
            await interaction.followup.send(f"⚠️ Failed to write or send export file: {e}", ephemeral=True)


    @app_commands.command(name="sangcleanup", description="Delete auto-created SanguineSunday voice channels from the last run.")
    @app_commands.checks.has_any_role("Administrators", "Clan Staff", "Senior Staff", "Staff", "Trial Staff")
    async def sangcleanup(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild
        category = guild.get_channel(SANG_VC_CATEGORY_ID)
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.followup.send("⚠️ Sanguine VC Category not found or is not a category.", ephemeral=True); return

        deleted_count = 0
        errors = 0
        # Iterate over a copy of the list as we are modifying it
        for ch in list(category.voice_channels):
            try:
                # Check name prefix and ensure it's a voice channel
                if ch.name.startswith("SanguineSunday – Team "):
                    await ch.delete(reason="SanguineSunday cleanup command")
                    deleted_count += 1
            except discord.Forbidden:
                 print(f"Cleanup Error: Missing permissions to delete {ch.name}")
                 errors += 1
            except Exception as e:
                 print(f"Cleanup Error: Failed to delete {ch.name}: {e}")
                 errors += 1

        response_message = f"🧹 Deleted {deleted_count} voice channel(s)."
        if errors > 0:
             response_message += f" Failed to delete {errors} channel(s) (check permissions/logs)."

        await interaction.followup.send(response_message, ephemeral=True)

    # --- Error Handler for Cog Commands ---
    @sangsignup.error
    @sangmatch.error
    @sangmatchtest.error
    @sangexport.error
    @sangcleanup.error
    async def sang_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Generic error handler for Sanguine commands."""
        original_error = getattr(error, 'original', error)

        if isinstance(original_error, app_commands.MissingRole):
            await interaction.response.send_message("❌ You don't have the required role (`Clan Staff`) for this command.", ephemeral=True)
        elif isinstance(original_error, discord.errors.NotFound):
             # Handle cases where interaction might expire
             print(f"Interaction expired or not found: {original_error}")
             try:
                 await interaction.followup.send("⚠️ Interaction timed out or could not be found.", ephemeral=True)
             except: pass # Ignore if followup also fails
        else:
            # Log the full error for debugging
            print(f"Error in a Sanguine command '{interaction.command.name}': {original_error}")
            traceback.print_exception(type(original_error), original_error, original_error.__traceback__)

            # Send a generic error message to the user
            error_message = f"An unexpected error occurred while running `/{interaction.command.name}`. Please notify staff."
            if interaction.response.is_done():
                try:
                    await interaction.followup.send(error_message, ephemeral=True)
                except: pass # Ignore if followup fails
            else:
                try:
                    await interaction.response.send_message(error_message, ephemeral=True)
                except: pass # Ignore if initial response fails


    # --- Scheduled Tasks ---

    # Runs every Friday at 11:00 AM Central Time
    @tasks.loop(time=dt_time(hour=11, minute=0, tzinfo=CST))
    async def scheduled_post_signup(self):
        # Check if today is Friday (0=Mon, 4=Fri)
        if datetime.now(CST).weekday() == 4:
            print("It's Friday at 11:00 AM CST. Posting Sanguine signup...")
            channel = self.bot.get_channel(SANG_POST_CHANNEL_ID)
            if channel:
                await self.post_signup(channel)
            else:
                print(f"🔥 Failed to post signup: Channel {SANG_POST_CHANNEL_ID} not found.")

    # Runs every Saturday at 2:00 PM Central Time
    @tasks.loop(time=dt_time(hour=14, minute=0, tzinfo=CST))
    async def scheduled_post_reminder(self):
        # Check if today is Saturday (5=Sat)
        if datetime.now(CST).weekday() == 5:
            print("It's Saturday at 2:00 PM CST. Posting Sanguine learner reminder...")
            channel = self.bot.get_channel(SANG_POST_CHANNEL_ID)
            if channel:
                await self.post_reminder(channel)
            else:
                print(f"🔥 Failed to post reminder: Channel {SANG_POST_CHANNEL_ID} not found.")

    # Runs every Monday at 4:00 AM Central Time
    @tasks.loop(time=dt_time(hour=4, minute=0, tzinfo=CST))
    async def scheduled_clear_sang_sheet(self):
        # Check if today is Monday (0=Mon)
        if datetime.now(CST).weekday() == 0:
            print("MONDAY DETECTED: Clearing SangSignups sheet...")
            if self.sang_sheet:
                try:
                    # Delete all rows except the header
                    self.sang_sheet.delete_rows(2, self.sang_sheet.row_count)
                    # Optional: Re-append header if clear() was used or sheet might be empty
                    # self.sang_sheet.append_row(SANG_SHEET_HEADER)
                    print("✅ SangSignups sheet cleared (keeping header).")
                except Exception as e:
                    print(f"🔥 Failed to clear SangSignups sheet: {e}")
            else:
                print("⚠️ Cannot clear SangSignups sheet, not connected.")

    # Wait until the bot is ready before starting the loops
    @scheduled_post_signup.before_loop
    @scheduled_post_reminder.before_loop
    @scheduled_clear_sang_sheet.before_loop
    async def before_scheduled_tasks(self):
        await self.bot.wait_until_ready()
        print("SanguineCog: Bot ready, scheduled tasks starting.")


# This setup function is required for the bot to load the Cog
async def setup(bot: commands.Bot):
    # Ensure GSheet variables are present before trying to add cog
    required_env = ['GOOGLE_TYPE', 'GOOGLE_PROJECT_ID', 'GOOGLE_PRIVATE_KEY_ID', 'GOOGLE_PRIVATE_KEY', 'GOOGLE_CLIENT_EMAIL', 'GOOGLE_CLIENT_ID', 'GOOGLE_AUTH_URI', 'GOOGLE_TOKEN_URI', 'GOOGLE_AUTH_PROVIDER_X509_CERT_URL', 'GOOGLE_CLIENT_X509_CERT_URL', 'GOOGLE_UNIVERSE_DOMAIN']
    missing_env = [var for var in required_env if not os.getenv(var)]
    if missing_env:
        print(f"🔥 CRITICAL ERROR: Cannot load SanguineCog. Missing environment variables: {', '.join(missing_env)}")
        return # Prevent loading if GSheet config is missing

    # Add the cog
    import traceback # Import traceback here for the error handler
    await bot.add_cog(SanguineCog(bot))
    print("SanguineCog added successfully.")
