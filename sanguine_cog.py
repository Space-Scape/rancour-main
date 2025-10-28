    @commands.Cog.listener()
    async def on_ready(self):
        """Called when the cog is loaded and the bot is ready."""
        # Start the tasks
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

        # guild = self.bot.get_channel(GUILD_ID).guild <--- REMOVED THIS LINE
        
        current_embed = discord.Embed(title=title, description=description, color=color)
        embeds.append(current_embed)
        field_count = 0
        
        # Define a safe limit for fields per embed. 25 is the max count,
        # but 10 is safer to avoid the 6000-character total embed limit.
        FIELDS_PER_EMBED = 10
        
        for i, team in enumerate(teams, start=1):
            if field_count >= FIELDS_PER_EMBED:
                # Current embed is full, create a new one
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

    def get_previous_signup(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetches the latest signup data for a user from the HISTORY sheet."""
        if not self.history_sheet:
            print("History sheet not available in get_previous_signup.")
            return None
        try:
            all_records = self.history_sheet.get_all_records()
            if not all_records:
                 print("No records found in history_sheet.")
                 return None
            
            # Iterate in reverse to find the *last* entry for this user
            for record in reversed(all_records):
                sheet_discord_id = record.get("Discord_ID")
                sheet_discord_id_str = str(sheet_discord_id) if sheet_discord_id is not None else None
                
                if sheet_discord_id_str == user_id:
                    # Convert GSheet "TRUE"/"FALSE" strings to real booleans
                    record["Has_Scythe"] = str(record.get("Has_Scythe", "FALSE")).upper() == "TRUE"
                    record["Learning Freeze"] = str(record.get("Learning Freeze", "FALSE")).upper() == "TRUE"
                    return record
            
            print(f"No history match found for user_id: {user_id}")
            return None
        except Exception as e:
            print(f"🔥 GSpread error fetching previous signup for {user_id}: {e}")
            return None

    async def post_signup(self, channel: discord.TextChannel):
        """Posts the main signup message with the signup buttons."""
        await channel.send(SANG_MESSAGE, view=SignupView(self))
        print(f"✅ Posted Sanguine Sunday signup in #{channel.name}")

    async def post_reminder(self, channel: discord.TextChannel):
        """Finds learners and posts a reminder."""
        if not self.sang_sheet:
            print("⚠️ Cannot post reminder, Sang Sheet not connected.")
            return False
        
        # Delete previous reminder messages
        try:
            async for message in channel.history(limit=50):
                if message.author == self.bot.user and LEARNER_REMINDER_IDENTIFIER in message.content:
                    await message.delete()
        except discord.Forbidden:
            print(f"⚠️ Could not delete old reminders in #{channel.name}")
        except Exception as e:
            print(f"🔥 Error cleaning up reminders: {e}")

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
            print(f"✅ Posted Sanguine Sunday learner reminder in #{channel.name}")
            return True
        except Exception as e:
            print(f"🔥 GSpread error fetching/posting reminder: {e}")
            await channel.send("⚠️ Error processing learner list from database.")
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
        target_channel = channel or self.bot.get_channel(SANG_CHANNEL_ID)
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
        await interaction.response.defer(ephemeral=False)
        
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
                 continue # User is not in the specified VC
            
            roles_str = signup.get("Favorite Roles", "")
            knows_range, knows_melee = parse_roles(roles_str)
            kc_raw = signup.get("KC", 0)
            
            try:
                kc_val = int(kc_raw)
            except (ValueError, TypeError):
                # Handle "X" KC for mentors or bad data
                kc_val = 9999 if signup.get("Proficiency", "").lower() == 'mentor' else 0
            
            proficiency_val = signup.get("Proficiency", "").lower()
            
            # Re-calculate proficiency based on KC, overriding sheet value
            # (unless they are a mentor)
            if proficiency_val != 'mentor':
                if kc_val <= 10: proficiency_val = "new"
                elif 11 <= kc_val <= 25: proficiency_val = "learner"
                elif 26 <= kc_val <= 100: proficiency_val = "proficient"
                else: proficiency_val = "highly proficient"

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
                "wants_mentor": str(signup.get("Mentor_Request", "FALSE")).upper() == "TRUE"
            })

        if not available_raiders:
            await interaction.followup.send(f"⚠️ None of the users in {voice_channel.mention} have signed up for the event." if voice_channel else "⚠️ No eligible signups.")
            return

        teams, stranded_players = matchmaking_algorithm(available_raiders)
        
        guild = interaction.guild
        category = guild.get_channel(SANG_VC_CATEGORY_ID)
        
        # Create Voice Channels
        if category and hasattr(category, "create_voice_channel"):
            for i in range(len(teams)):
                try:
                    await category.create_voice_channel(name=f"SanguineSunday – Team {i+1}", user_limit=5)
                except Exception as e:
                    print(f"Error creating VC: {e}") 

        post_channel = interaction.channel
        
        # --- Create Embeds ---
        embed_title = f"Sanguine Sunday Teams - {channel_name}"
        embed_desc = f"Created {len(teams)} valid team(s) from {len(available_raiders)} available signed-up users."
        
        team_embeds = await self._create_team_embeds(
            teams,
            embed_title,
            embed_desc,
            discord.Color.red(),
            guild,
            format_player_line_mention # Use the pinging formatter
        )
        
        global last_generated_teams
        last_generated_teams = teams

        # --- Send Embeds (one at a time) ---
        for i, embed in enumerate(team_embeds):
            if i == 0:
                await interaction.followup.send(embed=embed)
            else:
                # Send subsequent chunks as new messages
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
                elif 11 <= kc_val <= 25: proficiency_val = "learner"
                elif 26 <= kc_val <= 100: proficiency_val = "proficient"
                else: proficiency_val = "highly proficient"

            available_raiders.append({
                "user_id": user_id, "user_name": sanitize_nickname(signup.get("Discord_Name")),
                "proficiency": proficiency_val, "kc": kc_val,
                "has_scythe": str(signup.get("Has_Scythe", "FALSE")).upper() == "TRUE",
                "roles_known": roles_str, "learning_freeze": str(signup.get("Learning Freeze", "FALSE")).upper() == "TRUE",
                "knows_range": knows_range, "knows_melee": knows_melee,
                "wants_mentor": str(signup.get("Mentor_Request", "FALSE")).upper() == "TRUE"
            })
        
        if not available_raiders:
            await interaction.followup.send("⚠️ No eligible signups.")
            return

        teams, stranded_players = matchmaking_algorithm(available_raiders)
        
        guild = interaction.guild
        post_channel = channel or interaction.channel

        # --- Create Embeds ---
        embed_title = f"Sanguine Sunday Teams (Test, no pings/VC) - {channel_name}"
        embed_desc = f"Created {len(teams)} valid team(s) from {len(available_raiders)} available signed-up users."

        team_embeds = await self._create_team_embeds(
            teams,
            embed_title,
            embed_desc,
            discord.Color.dark_gray(),
            guild,
            format_player_line_plain # Use the NO-ping formatter
        )

        global last_generated_teams
        last_generated_teams = teams
        
        # --- Send Embeds (one at a time) ---
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

        # Try to save to a mounted volume, fallback to /tmp
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


    @app_commands.command(name="sangcleanup", description="Delete auto-created SanguineSunday voice channels from the last run.")
    @app_commands.checks.has_any_role("Administrators", "Clan Staff", "Senior Staff", "Staff", "Trial Staff")
    async def sangcleanup(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild
        category = guild.get_channel(SANG_VC_CATEGORY_ID)
        if not category:
            await interaction.followup.send("⚠️ Category not found.", ephemeral=True); return
        deleted = 0
        for ch in list(category.channels):
            try:
                if isinstance(ch, discord.VoiceChannel) and ch.name.startswith("SanguineSunday – Team "):
                    await ch.delete(reason="sangcleanup")
                    deleted += 1
            except Exception:
                pass # Ignore errors (e.g., channel deleted by someone else)
        await interaction.followup.send(f"🧹 Deleted {deleted} voice channels.", ephemeral=True)

    @sangsignup.error
    @sangmatch.error
    @sangmatchtest.error
    @sangexport.error
    @sangcleanup.error
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

    @tasks.loop(time=dt_time(hour=14, minute=0, tzinfo=CST))
    async def scheduled_post_reminder(self):
        if datetime.now(CST).weekday() == 5:  # 5 = Saturday
            print("It's Saturday at 2:00 PM CST. Posting Sanguine learner reminder...")
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
                except Exception as e:
                    print(f"🔥 Failed to clear SangSignups sheet: {e}")
            else:
                print("⚠️ Cannot clear SangSignups sheet, not connected.")

    @scheduled_post_signup.before_loop
    @scheduled_post_reminder.before_loop
    @scheduled_clear_sang_sheet.before_loop
    async def before_scheduled_tasks(self):
        await self.bot.wait_until_ready()

# This setup function is required for the bot to load the Cog
async def setup(bot: commands.Bot):
    await bot.add_cog(SanguineCog(bot))
