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

def is_blacklist_violation(player: Dict[str, Any], team: List[Dict[str, Any]]) -> bool:
    """Checks if a player joining a team violates any blacklists."""
    player_blacklist = player.get("blacklist", set())
    player_id_str = str(player.get("user_id"))
    
    for p_in_team in team:
        p_in_team_id_str = str(p_in_team.get("user_id"))
        
        # Check 1: Does the player on the team (a mentor) exist in the new player's blacklist?
        if p_in_team_id_str in player_blacklist:
            return True # Player blacklists someone on team

        # Check 2: Does the new player (a mentor) exist in the team member's blacklist?
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

    strong_pool = [p for p in non_mentors if prof_rank(p) <= PROF_ORDER["proficient"]]    # HP/Pro
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
            sizes = [4]*q + ([3] if r == 3 else ([] if r == 0 else [4]))

    T = len(sizes) # Total number of teams

    # ---------- Build anchors (Mentors first, then strongest HP/Pro) ----------
    anchors: List[Optional[Dict[str, Any]]] = [None] * T
    teams: List[List[Dict[str, Any]]] = []
    
    anchor_pools_normal = [mentors, strong_pool, learners, news, mentees]
    anchor_pools_trio = [strong_pool, learners, news, mentees]
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
            teams.append([])

    extra_mentors = mentors

    # ---------- Helper for safe placement ----------
    def can_add(player, team, max_size) -> bool:
        """Checks if a player can be added to a team based on constraints."""
        if len(team) >= max_size:
            return False
        
        # --- NEW: Blacklist Check ---
        if is_blacklist_violation(player, team):
            return False # Player or team member is on a blacklist

        future_size = len(team) + 1

        if max_size == 3:
            if normalize_role(player) == "mentor":
                return False
            if not is_proficient_plus(player):
                return False
            if not all(is_proficient_plus(p) for p in team):
                return False
        
        if player.get('learning_freeze') and any(p.get('learning_freeze') for p in team):
            return False
                
        if (normalize_role(player) == "new" or player.get("wants_mentor")) and not any(normalize_role(p) == "mentor" for p in team):
             return False # BLOCK: No mentor on team.

        return True

    max_sizes = list(sizes) # [5, 4, 4]

    # ---------- Place mentees onto Mentor teams first ----------
    mentor_idxs = [i for i, t in enumerate(teams) if normalize_role(t[0]) == "mentor"]
    mentees.sort(key=lambda p: (prof_rank(p), not p.get("has_scythe"), -int(p.get("kc", 0))))
    if mentor_idxs and mentees:
        forward = True
        while mentees:
            placed = False
            idxs = mentor_idxs if forward else mentor_idxs[::-1]
            forward = not forward
            
            for i in idxs:
                if can_add(mentees[0], teams[i], max_sizes[i]):
                    teams[i].append(mentees.pop(0))
                    placed = True
                    break
            
            if not placed:
                break

    # ---------- Distribute leftovers ----------
    leftovers = strong_pool + learners + news + mentees + extra_mentors
    forward = True
    safety = 0
    while leftovers and safety < 10000:
        safety += 1
        placed_any = False
        idxs = list(range(T)) if forward else list(range(T-1, -1, -1))
        forward = not forward
        
        for i in idxs:
            if not leftovers:
                break
            if can_add(leftovers[0], teams[i], max_sizes[i]):
                teams[i].append(leftovers.pop(0))
                placed_any = True
        
        if not placed_any:
            need_idxs = [i for i in range(T) if max_sizes[i] == 3 and len(teams[i]) < 3]
            borrowed = False
            for ti in need_idxs:
                for dj in range(T):
                    if dj == ti: continue
                    donor_min_keep = 5 if max_sizes[dj] == 5 else (4 if max_sizes[dj] == 4 else 3)
                    if len(teams[dj]) <= donor_min_keep: continue
                    
                    donor = next((p for p in teams[dj] if is_proficient_plus(p)), None)
                    if donor and can_add(donor, teams[ti], max_sizes[ti]):
                        teams[ti].append(donor)
                        teams[dj].remove(donor)
                        borrowed = True
                        placed_any = True
                        break
                if borrowed: break
            
            if not placed_any:
                leftovers.append(leftovers.pop(0))
    
    # --- Phase 4: Resolve Stranded "New" Players (SWAP LOGIC) ---
    final_stranded = []
    for player in leftovers:
        is_new_or_mentee = normalize_role(player) == "new" or player.get("wants_mentor")
        
        if not is_new_or_mentee:
            # This player is a "Learner" or "Proficient"
            placed = False
            for i in range(T):
                # We can safely bypass the "can_add" mentor check here,
                # but we must still check the blacklist.
                if len(teams[i]) < max_sizes[i] and not is_blacklist_violation(player, teams[i]):
                    teams[i].append(player)
                    placed = True
                    break
            if not placed:
                final_stranded.append(player)
            continue

        # --- This player IS a "New" player or "Mentee" ---
        placed = False
        for i in range(T):
            team_has_mentor = any(normalize_role(p) == "mentor" for p in teams[i])
            if team_has_mentor and can_add(player, teams[i], max_sizes[i]): # can_add checks blacklist
                 teams[i].append(player)
                 placed = True
                 break
        
        if placed:
            continue
            
        if not placed:
            swapped = False
            for i in range(T):
                team_has_mentor = any(normalize_role(p) == "mentor" for p in teams[i])
                if not team_has_mentor:
                    continue

                learner_to_swap = None
                for p_in_team in teams[i]:
                    if normalize_role(p_in_team) == "learner":
                        learner_to_swap = p_in_team
                        break
                
                if learner_to_swap:
                    # Found a swap!
                    # 1. Check if the "New" player can join the mentor team (blacklist check)
                    temp_mentor_team = [p for p in teams[i] if p != learner_to_swap]
                    if is_blacklist_violation(player, temp_mentor_team):
                        continue # This swap violates blacklist, try next team

                    # 2. Find a new home for the "Learner"
                    new_home_for_learner = None
                    for j in range(T):
                        if i == j: continue
                        # Learner can join non-mentor team, but must check blacklist
                        if len(teams[j]) < max_sizes[j] and not is_blacklist_violation(learner_to_swap, teams[j]):
                            new_home_for_learner = teams[j]
                            break
                    
                    if new_home_for_learner:
                        # Swap is possible
                        teams[i].remove(learner_to_swap)
                        teams[i].append(player)
                        new_home_for_learner.append(learner_to_swap)
                        swapped = True
                        break

            if swapped:
                continue

        if not placed and not swapped:
            # FINAL FALLBACK: No mentor teams had space, no swaps possible.
            for i in range(T):
                # Must use can_add to check blacklist, even here
                if can_add(player, teams[i], max_sizes[i]):
                    teams[i].append(player)
                    placed = True
                    break
            
            if not placed:
                final_stranded.append(player)
    
    # --- Phase 5: Balance "New" Player KC across Mentor Teams ---
    mentor_teams = [t for t in teams if any(normalize_role(p) == "mentor" for p in t)]
    if len(mentor_teams) > 1:
        def get_new_player_kc(team):
            return sum(int(p.get("kc", 0)) for p in team if normalize_role(p) == "new")
            
        mentor_teams.sort(key=get_new_player_kc)
        
        lowest_team = mentor_teams[0]
        highest_team = mentor_teams[-1]
        
        if get_new_player_kc(highest_team) > get_new_player_kc(lowest_team):
            new_from_high = sorted([p for p in highest_team if normalize_role(p) == "new"], key=lambda p: -int(p.get("kc", 0)))
            new_from_low = sorted([p for p in lowest_team if normalize_role(p) == "new"], key=lambda p: int(p.get("kc", 0)))

            if new_from_high and new_from_low:
                player_to_move_up = new_from_high[0]
                player_to_move_down = new_from_low[0]
                
                if int(player_to_move_up.get("kc", 0)) > int(player_to_move_down.get("kc", 0)):
                    # --- Blacklist check before swapping ---
                    temp_lowest_team = [p for p in lowest_team if p != player_to_move_down]
                    temp_highest_team = [p for p in highest_team if p != player_to_move_up]
                    
                    violates_lowest = is_blacklist_violation(player_to_move_up, temp_lowest_team)
                    violates_highest = is_blacklist_violation(player_to_move_down, temp_highest_team)

                    if not violates_lowest and not violates_highest:
                        # Perform the swap
                        lowest_team.remove(player_to_move_down)
                        lowest_team.append(player_to_move_up)
                        highest_team.remove(player_to_move_up)
                        highest_team.append(player_to_move_down)
                        print(f"Balancing Swap: Moved {player_to_move_up.get('user_name')} to {lowest_team[0].get('user_name')}'s team.")
                        print(f"Balancing Swap: Moved {player_to_move_down.get('user_name')} to {highest_team[0].get('user_name')}'s team.")

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
# ... (this class is correct, no changes) ...
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
        
        blacklist_value = self.previous_data.get("Blacklist", "") if self.previous_data else ""
        
        row_data = [user_id, user_name, roles_known_value, kc_value, has_scythe_bool, proficiency_value, learning_freeze_bool, wants_mentor_bool, timestamp, blacklist_value]
        
        # --- FIXED LOGIC: Parallel Sheet Updates ---
        
        sang_sheet_success = False
        history_sheet_success = False

        # Operation 1: Write to SangSignups Sheet
        try:
            cell = self.cog.sang_sheet.find(user_id, in_column=1)
            self.cog.sang_sheet.update(values=[row_data], range_name=f'A{cell.row}:J{cell.row}')
            sang_sheet_success = True
        except gspread.CellNotFound:
            try:
                self.cog.sang_sheet.append_row(row_data)
                sang_sheet_success = True
            except Exception as e:
                print(f"🔥 GSpread error on SangSignups APPEND: {e}")
        except Exception as e:
            print(f"🔥 GSpread error on SangSignups UPDATE: {e}")

        # Operation 2: Write to History Sheet
        if self.cog.history_sheet:
            try:
                history_cell = self.cog.history_sheet.find(user_id, in_column=1)
                self.cog.history_sheet.update(values=[row_data], range_name=f'A{history_cell.row}:J{history_cell.row}')
                history_sheet_success = True
            except gspread.CellNotFound:
                try:
                    self.cog.history_sheet.append_row(row_data)
                    history_sheet_success = True
                except Exception as e:
                    print(f"🔥 GSpread error on History APPEND: {e}")
            except Exception as e:
                print(f"🔥 GSpread error on History UPDATE: {e}")
        else:
            print("🔥 History sheet not available, skipping history write.")
            history_sheet_success = True # Don't block success if history is down

        # --- End Fixed Logic ---

        if sang_sheet_success and history_sheet_success:
            await interaction.response.send_message(
                f"✅ **You are signed up as {proficiency_value}!**\n"
                f"**KC:** {kc_value}\n"
                f"**Scythe:** {'Yes' if has_scythe_bool else 'No'}\n"
                f"**Favorite Roles:** {roles_known_value}\n"
                f"**Learn Freeze:** {'Yes' if learning_freeze_bool else 'No'}\n"
                f"**Mentor Request:** {'Yes' if wants_mentor_bool else 'No'}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("⚠️ An error occurred while saving your signup. Please contact staff.", ephemeral=True)


class MentorSignupForm(Modal, title="Sanguine Sunday Mentor Signup"):
# ... (this class is correct, no changes) ...
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
        
        blacklist_value = self.previous_data.get("Blacklist", "") if self.previous_data else ""
        
        row_data = [user_id, user_name, roles_known_value, kc_value, has_scythe_bool, proficiency_value, learning_freeze_bool, False, timestamp, blacklist_value]
        
        # --- FIXED LOGIC: Parallel Sheet Updates ---

        sang_sheet_success = False
        history_sheet_success = False

        # Operation 1: Write to SangSignups Sheet
        try:
            cell = self.cog.sang_sheet.find(user_id, in_column=1)
            self.cog.sang_sheet.update(values=[row_data], range_name=f'A{cell.row}:J{cell.row}')
            sang_sheet_success = True
        except gspread.CellNotFound:
            try:
                self.cog.sang_sheet.append_row(row_data)
                sang_sheet_success = True
            except Exception as e:
                print(f"🔥 GSpread error on SangSignups (Mentor) APPEND: {e}")
        except Exception as e:
            print(f"🔥 GSpread error on SangSignups (Mentor) UPDATE: {e}")

        # Operation 2: Write to History Sheet
        if self.cog.history_sheet:
            try:
                history_cell = self.cog.history_sheet.find(user_id, in_column=1)
                self.cog.history_sheet.update(values=[row_data], range_name=f'A{history_cell.row}:J{history_cell.row}')
                history_sheet_success = True
            except gspread.CellNotFound:
                try:
                    self.cog.history_sheet.append_row(row_data)
                    history_sheet_success = True
                except Exception as e:
                    print(f"🔥 GSpread error on History (Mentor) APPEND: {e}")
            except Exception as e:
                print(f"🔥 GSpread error on History (Mentor) UPDATE: {e}")
        else:
            print("🔥 History sheet not available, skipping history write.")
            history_sheet_success = True # Don't block success if history is down
            
        # --- End Fixed Logic ---

        if sang_sheet_success and history_sheet_success:
            await interaction.response.send_message(
                f"✅ **You are signed up as a Mentor!**\n"
                f"**KC:** {kc_value}\n"
                f"**Scythe:** {'Yes' if has_scythe_bool else 'No'}\n"
                f"**Favorite Roles:** {roles_known_value}",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("⚠️ An error occurred while saving your signup. Please contact staff.", ephemeral=True)


class WithdrawalButton(ui.Button):
# ... (this class is correct, no changes) ...
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

        # Get previous data regardless of role
        previous_data = self.cog.get_previous_signup(str(user.id))

        # --- SIMPLIFIED LOGIC ---
        # Everyone who clicks the Mentor button gets the Mentor form.
        # The form itself will validate KC.
        
        # If they previously auto-signed up (KC == "X")
        # clear the "X" so the placeholder text shows instead.
        if previous_data and previous_data.get("KC") == "X":
             previous_data["KC"] = "" 
             
        await interaction.response.send_modal(MentorSignupForm(self.cog, previous_data=previous_data))


# ---------------------------
# 🔹 Sanguine Cog Class
# ---------------------------

class SanguineCog(commands.Cog):
# ... (rest of the file is correct, no changes) ...
    @scheduled_clear_sang_sheet.before_loop
    async def before_scheduled_tasks(self):
        await self.bot.wait_until_ready()

# This setup function is required for the bot to load the Cog
async def setup(bot: commands.Bot):
    await bot.add_cog(SanguineCog(bot))

