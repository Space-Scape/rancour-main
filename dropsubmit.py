import os
import discord
from discord.ext import commands
from discord import app_commands
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from datetime import datetime, timezone
import asyncio

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

# ---------------------------
# 🔹 Boss-Drop Mapping
# ---------------------------

boss_drops = {
    "Abyssal Sire": ["Abyssal orphan", "Unsired", "Abyssal head", "Bludgeon spine", "Bludgeon claw", "Bludgeon axon", "Jar of miasma", "Abyssal dagger", "Abyssal whip"],
    "Alchemical Hydra": ["Ikkle hydra", "Hydra's claw", "Hydra tail", "Hydra leather", "Hydra's fang", "Hydra's eye", "Hydra's heart", "Dragon knife", "Dragon thrownaxe", "Jar of chemicals", "Alchemical hydra heads"],
    "Amoxliatl": ["Moxi", "Glacial temotli", "Pendant of ates (inert)", "Frozen tear"],
    "Araxxor": ["Noxious pommel", "Noxious point", "Noxious blade", "Araxyte fang", "Araxyte head", "Jar of venom", "Coagulated venom", "Nid"],
    "Artio": ["Callisto cub", "Tyrannical ring", "Dragon pickaxe", "Dragon 2h sword", "Claws of callisto", "Voidwaker hilt"],
    "Barrows": ["Ahrim's hood", "Ahrim's robetop", "Ahrim's robeskirt", "Ahrim's staff", "Karil's coif", "Karil's leathertop", "Karil's leatherskirt", "Karil's crossbow", "Dharok's helm", "Dharok's platebody", "Dharok's platelegs", "Dharok's greataxe", "Guthan's helm", "Guthan's platebody", "Guthan's chainskirt", "Guthan's warspear", "Torag's helm", "Torag's platebody", "Torag's platelegs", "Torag's hammers", "Verac's helm", "Verac's brassard", "Verac's plateskirt", "Verac's flail"],
    "Bryophyta": ["Bryophyta's essence"],
    "Callisto": ["Callisto cub", "Tyrannical ring", "Dragon pickaxe", "Dragon 2h sword", "Claws of callisto", "Voidwaker hilt"],
    "Cerberus": ["Hellpuppy", "Eternal crystal", "Pegasian crystal", "Primordial crystal", "Jar of souls", "Smouldering stone", "Key master teleport"],
    "Chaos Elemental": ["Pet chaos elemental", "Dragon pickaxe", "Dragon 2h sword"],
    "Chaos Fanatic": ["Pet chaos elemental", "Odium shard 1", "Malediction shard 1"],
    "Chambers of Xeric": ["Dexterous prayer scroll", "Arcane prayer scroll", "Twisted buckler", "Dragon hunter crossbow", "Dinh's bulwark", "Ancestral hat", "Ancestral robe top", "Ancestral robe bottom", "Dragon claws", "Elder maul", "Kodai insignia", "Twisted bow", "Olmlet", "Twisted ancestral colour kit", "Metamorphic dust"],
    "Colosseum": ["Smol heredit", "Dizana's quiver (uncharged)", "Sunfire fanatic cuirass", "Sunfire fanatic chausses", "Sunfire fanatic helm", "Echo crystal", "Tonalztics of ralos (uncharged)", "Sunfire splinters"],
    "Commander Zilyana": ["Pet zilyana", "Armadyl crossbow", "Saradomin hilt", "Saradomin sword", "Saradomin's light", "Godsword shard 1", "Godsword shard 2", "Godsword shard 3"],
    "Corporeal Beast": ["Pet dark core", "Elysian sigil", "Spectral sigil", "Arcane sigil", "Spirit shield", "Holy elixir", "Jar of spirits"],
    "Crazy Archaeologist": ["Odium shard 2", "Malediction shard 2", "Fedora"],
    "Dagannoth Kings": ["Pet dagannoth supreme", "Pet dagannoth rex", "Pet dagannoth prime", "Archers ring", "Seers ring", "Berserker ring", "Warrior ring", "Dragon axe", "Seercull", "Mud battlestaff"],
    "Deranged Archaeologist": ["Steel ring"],
    "Duke Sucellus": ["Baron", "Virtus mask", "Virtus robe top", "Virtus robe bottom", "Chromium ingot", "Awakener's orb", "Magus vestige", "Eye of the duke", "Ice quartz", "Frozen tablet"],
    "Gauntlet": ["Youngllef", "Crystal weapon seed", "Crystal armour seed", "Enhanced crystal weapon seed"],
    "General Graardor": ["Pet general graardor", "Bandos hilt", "Bandos chestplate", "Bandos tassets", "Bandos boots", "Godsword shard 1", "Godsword shard 2", "Godsword shard 3"],
    "Giant Mole": ["Baby mole", "Mole claw", "Mole skin"],
    "Grotesque Guardians": ["Noon", "Granite gloves", "Granite hammer", "Granite ring", "Black tourmaline core", "Jar of stone"],
    "Hueycoatl": ["Huberte", "Dragon hunter wand", "Hueycoatl hide", "Tome of earth (empty)"],
    "Inferno": ["Jal-nib-rek", "Infernal cape"],
    "Jad": ["Tzrek-jad", "Fire cape"],
    "Kalphite Queen": ["Kalphite princess", "Dragon chainbody", "Dragon pickaxe", "Dragon 2h sword", "Jar of sand", "Kq head"],
    "Kraken": ["Pet kraken", "Kraken tentacle", "Trident of the seas (full)", "Jar of dirt"],
    "Kree'arra": ["Pet kree'arra", "Armadyl helmet", "Armadyl chestplate", "Armadyl chainskirt", "Armadyl hilt", "Godsword shard 1", "Godsword shard 2", "Godsword shard 3"],
    "Moons of Peril": ["Eclipse atlatl", "Eclipse moon helm", "Eclipse moon chestplate", "Eclipse moon tassets", "Dual macuahuitl", "Blood moon helm", "Blood moon chestplate", "Blood moon tassets", "Blue moon spear", "Blue moon helm", "Blue moon chestplate", "Blue moon tassets"],
    "Nightmare": ["Little nightmare", "Nightmare staff", "Inquisitor's great helm", "Inquisitor's hauberk", "Inquisitor's plateskirt", "Inquisitor's mace", "Eldritch orb", "Harmonised orb", "Volatile orb"],
    "Nex": ["Nexling", "Ancient hilt", "Nihil horn", "Zaryte vambraces", "Torva full helm (damaged)", "Torva platebody (damaged)", "Torva platelegs (damaged)"],
    "Phantom Muspah": ["Muphin", "Venator shard", "Ancient icon", "Charged ice", "Frozen cache", "Ancient essence"],
    "Royal Titans": ["Bran", "Deadeye prayer scroll", "Mystic vigour prayer scroll", "Fire element staff crown", "Ice element staff crown", "Giantsoul amulet", "Desiccated page"],
    "Sarachnis": ["Sraracha", "Sarachnis cudgel", "Giant egg sac", "Jar of eyes"],
    "Scurrius": ["Scurry", "Scurrius' spine"],
    "The Leviathan": ["Lil'viathan", "Virtus mask", "Virtus robe top", "Virtus robe bottom", "Chromium ingot", "Awakener's orb", "Venator vestige", "Leviathan's lure", "Smoke quartz", "Scarred tablet"],
    "The Whisperer": ["Wisp", "Virtus mask", "Virtus robe top", "Virtus robe bottom", "Chromium ingot", "Awakener's orb", "Bellator vestige", "Siren's staff", "Shadow quartz", "Sirenic tablet"],
    "Theatre of Blood": ["Lil' zik", "Avernic defender hilt", "Ghrazi rapier", "Sanguinesti staff (uncharged)", "Justiciar faceguard", "Justiciar chestguard", "Justiciar legguards", "Scythe of vitur (uncharged)", "Holy ornament kit", "Sanguine ornament kit", "Sanguine dust"],
    "Tombs of Amascut": ["Masori mask", "Masori body", "Masori chaps", "Lightbearer", "Osmumten's fang", "Elidinis' ward", "Tumeken's shadow (uncharged)"],
    "Tormented Demons": ["Tormented synapse", "Burning claw"],
    "Vardorvis": ["Butch", "Virtus mask", "Virtus robe top", "Virtus robe bottom", "Chromium ingot", "Awakener's orb", "Ultor vestige", "Executioner's axe head", "Blood quartz", "Strangled tablet"],
    "Venenatis": ["Venenatis spiderling", "Fangs of venenatis", "Dragon 2h sword", "Dragon pickaxe", "Voidwaker gem", "Treasonous ring"],
    "Vet'ion": ["Vet'ion jr.", "Skull of vet'ion", "Dragon 2h sword", "Dragon pickaxe", "Voidwaker blade", "Ring of the gods", "Skeleton champion scroll"],
    "Vorkath": ["Vorki", "Vorkath's head", "Draconic visage", "Serpentine visage", "Jar of decay", "Dragonbone necklace"],
    "Yama": ["Yami", "Soulflame horn", "Oathplate helm", "Oathplate chest", "Oathplate legs", "Oathplate shards", "Barrel of demonic tallow", "Forgotten lockbox", "Dossier", "Aether catalyst", "Diabolic worms", "Chasm teleport scroll"],
    "Zulrah": ["Pet snakeling", "Tanzanite mutagen", "Magma mutagen", "Jar of swamp water", "Tanzanite fang", "Magic fang", "Serpentine visage", "Uncut onyx"],
    "Varlamore Misc": ["Sulphur blades"],
    "Misthalin/wilderness Misc": ["Zombie helm", "Zombie axe", "Dragon limbs", "Dragon metal lump"],
    "Kourend/Kebos Misc": ["Pyromancer garb", "Pyromancer robe", "Pyromancer boots", "Tome of fire (empty)", "Phoenix", "Dragon axe", "Pyromancer hood", "Bruma torch", "Golden tench", "Warm gloves"],
    "Desert Misc": ["Kq head", "Pharaoh's sceptre (uncharged)", "500 toa kit", "Abyssal needle", "Abyssal lantern", "Abyssal red dye", "Abyssal green dye", "Abyssal blue dye"],
    "Asgarnia Misc": ["Dragon boots"],
    "Morytania Misc": ["Zealot’s helm", "Zealot’s robe top", "Zealot’s robe bottom", "Zealot’s boots"],
    "Tirannwn/fremennik Misc": ["Brine saber"],
}

# ---------------------------
# 🔹 Slash Command
# ---------------------------
@tree.command(name="submitdrop", description="Submit a boss drop for review")
@app_commands.describe(
    screenshot="Attach a screenshot of your drop",
    submitted_for="Optionally specify the user you're submitting this drop for"
)
async def submit_drop(interaction: discord.Interaction, screenshot: discord.Attachment, submitted_for: discord.Member = None):
    if interaction.channel.id != SUBMISSION_CHANNEL_ID:
        await interaction.response.send_message("❌ This command can only be used in the drop submission channel.", ephemeral=True)
        return

    # Use specified user or fallback to the command sender
    target_user = submitted_for or interaction.user

    await interaction.response.send_message(
        content=f"Submitting drop for {target_user.display_name}. Select the boss you received the drop from:",
        view=BossView(interaction.user, target_user, screenshot),
        ephemeral=True
    )

# The BossView manages boss pagination and selection
class BossSelect(discord.ui.Select):
    def __init__(self, submitting_user, target_user, screenshot, page=0):
        self.submitting_user = submitting_user
        self.target_user = target_user
        self.screenshot = screenshot
        self.page = page

        bosses = list(boss_drops.keys())
        max_pages = (len(bosses) - 1) // 25
        page = max(0, min(page, max_pages))

        page_bosses = bosses[page * 25: (page + 1) * 25]
        options = [discord.SelectOption(label=boss) for boss in page_bosses]

        super().__init__(placeholder="Select a boss", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        boss = self.values[0]
        await interaction.response.edit_message(
            content=f"Selected boss: {boss}. Now select the drop you received.",
            view=DropView(self.submitting_user, self.target_user, self.screenshot, boss)
        )

class BossView(discord.ui.View):
    def __init__(self, submitting_user, target_user, screenshot, page=0):
        super().__init__()
        self.add_item(BossSelect(submitting_user, target_user, screenshot, page))
        if page > 0:
            self.add_item(PreviousPageButton(submitting_user, target_user, screenshot, page))
        max_pages = (len(boss_drops) - 1) // 25
        if page < max_pages:
            self.add_item(NextPageButton(submitting_user, target_user, screenshot, page))

class PreviousPageButton(discord.ui.Button):
    def __init__(self, submitting_user, target_user, screenshot, page):
        super().__init__(label="◀️ Previous Page", style=discord.ButtonStyle.secondary)
        self.submitting_user = submitting_user
        self.target_user = target_user
        self.screenshot = screenshot
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=BossView(self.submitting_user, self.target_user, self.screenshot, self.page - 1))

class NextPageButton(discord.ui.Button):
    def __init__(self, submitting_user, target_user, screenshot, page):
        super().__init__(label="Next Page ▶️", style=discord.ButtonStyle.secondary)
        self.submitting_user = submitting_user
        self.target_user = target_user
        self.screenshot = screenshot
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=BossView(self.submitting_user, self.target_user, self.screenshot, self.page + 1))

# ---------------------------
# 🔹 Utility: Get team role mention
# ---------------------------
def get_team_role_mention(member: discord.Member) -> str:
    for role in member.roles:
        if role.name.startswith("Team "):
            return role.mention
    return "*No team*"

# ---------------------------
# 🔹 Drop Select
# ---------------------------
class DropSelect(discord.ui.Select):
    def __init__(self, submitting_user, target_user, screenshot, boss):
        self.submitting_user = submitting_user
        self.target_user = target_user
        self.screenshot = screenshot
        self.boss = boss
        options = [discord.SelectOption(label=drop) for drop in boss_drops[boss]]
        super().__init__(placeholder=f"Select a drop from {boss}", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        drop_name = self.values[0]
        review_channel = bot.get_channel(REVIEW_CHANNEL_ID)

        embed = discord.Embed(title=f"{self.boss} Drop Submission", colour=discord.Colour.blurple())
        embed.add_field(name="Submitted For", value=f"{self.target_user.mention} ({self.target_user.id})", inline=False)
        embed.add_field(name="Drop Received", value=drop_name, inline=False)
        embed.add_field(name="Submitted By", value=f"{self.submitting_user.mention} ({self.submitting_user.id})", inline=False)
        embed.set_image(url=self.screenshot.url)

        await interaction.response.edit_message(content="✅ Submitted for review.", embed=embed, view=None)

        if review_channel:
            team_mention = get_team_role_mention(self.target_user)
            await review_channel.send(
                embed=embed,
                view=DropReviewButtons(self.target_user, drop_name, self.screenshot.url, self.submitting_user, team_mention)
            )

class DropView(discord.ui.View):
    def __init__(self, submitting_user, target_user, screenshot, boss):
        super().__init__()
        self.add_item(DropSelect(submitting_user, target_user, screenshot, boss))

# ---------------------------
# 🔹 DropReviewButtons
# ---------------------------
class DropReviewButtons(discord.ui.View):
    def __init__(self, submitted_user: discord.Member, drop: str, image_url: str, submitting_user: discord.Member, team_mention: str):
        super().__init__(timeout=None)
        self.submitted_user = submitted_user
        self.drop = drop
        self.image_url = image_url
        self.submitting_user = submitting_user
        self.team_mention = team_mention

    def has_drop_manager_role(self, member: discord.Member) -> bool:
        return any(role.name == REQUIRED_ROLE_NAME for role in member.roles)

    @discord.ui.button(label="Approve ✅", style=discord.ButtonStyle.green)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.has_drop_manager_role(interaction.user):
            await interaction.response.send_message("❌ You do not have permission to approve.", ephemeral=True)
            return

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(title="Drop Approved", colour=discord.Colour.green())
            embed.add_field(name="Approved By", value=interaction.user.display_name, inline=False)
            embed.add_field(name="Drop For", value=self.submitted_user.mention, inline=False)
            embed.add_field(name="Team", value=self.team_mention, inline=False)
            embed.add_field(name="Drop", value=self.drop, inline=False)
            embed.add_field(name="Submitted By", value=self.submitting_user.mention, inline=False)
            embed.set_image(url=self.image_url)
            await log_channel.send(embed=embed)

        sheet.append_row([
            interaction.user.display_name,
            self.submitted_user.display_name,
            str(self.submitted_user.id),
            self.drop,
            self.image_url,
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        ])

        for child in self.children:
            child.disabled = True

        await interaction.message.edit(view=self)
        await interaction.response.send_message("✅ Approved and logged.", ephemeral=True)

    @discord.ui.button(label="Reject ❌", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.has_drop_manager_role(interaction.user):
            await interaction.response.send_message("❌ You do not have permission to reject.", ephemeral=True)
            return

        modal = RejectReasonModal(self, interaction)
        await interaction.response.send_modal(modal)

class RejectReasonModal(discord.ui.Modal, title="Reject Submission"):
    def __init__(self, parent_view: discord.ui.View, interaction: discord.Interaction):
        super().__init__()
        self.parent_view = parent_view
        self.message = interaction.message

        self.reason = discord.ui.TextInput(
            label="Reason for rejection",
            style=discord.TextStyle.paragraph,
            placeholder="Enter the reason why this drop is being rejected.",
            required=True,
            max_length=500
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(title="Drop Rejected", colour=discord.Colour.red())
            embed.add_field(name="Rejected By", value=interaction.user.display_name, inline=False)
            embed.add_field(name="Drop For", value=self.parent_view.submitted_user.mention, inline=False)
            embed.add_field(name="Team", value=self.parent_view.team_mention, inline=False)
            embed.add_field(name="Drop", value=self.parent_view.drop, inline=False)
            embed.add_field(name="Submitted By", value=self.parent_view.submitting_user.mention, inline=False)
            embed.add_field(name="Reason", value=self.reason.value, inline=False)
            embed.set_image(url=self.parent_view.image_url)
            await log_channel.send(embed=embed)

        for child in self.parent_view.children:
            child.disabled = True
        await self.message.edit(view=self.parent_view)

        await interaction.response.send_message("❌ Submission rejected with reason logged.", ephemeral=True)

# ---------------------------
# 🔹 Welcome#
# ---------------------------

@bot.tree.command(name="welcome", description="Welcome the ticket creator and give them the Recruit role.")
async def welcome(interaction: discord.Interaction):
    if not isinstance(interaction.channel, discord.Thread):
        await interaction.response.send_message("⚠️ This command must be used inside a ticket thread.", ephemeral=True)
        return

    # Scan message history for the Tickets v2 system message
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
        await interaction.response.send_message("⚠️ Could not detect who opened this ticket.", ephemeral=True)
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
            f"⚠️ Missing roles: {', '.join(missing_roles)}. Please check the server roles.", ephemeral=True
        )
        return

    welcome_message = (
        f":tada: Welcome to the Clan {ticket_creator.mention}! :tada:\n\n"
        f"We're thrilled to have you with us! :confetti_ball:\n"
        f"First and foremost, please make sure you visit our :scroll: "
        f"https://discord.com/channels/1272629330115297330/1272629843552501802 to ensure you're aware of the guidelines.\n\n"
        f"Below are some channels that will help you get started:\n\n"
        f":bulb: [Self-Role Assign](https://discord.com/channels/1272629330115297330/1272648586198519818)\n"
        f"-Select roles to be pinged for bosses and raids.\n"
        f":thought_balloon: [General Chat](https://discord.com/channels/1272629330115297330/1272629331524587623)\n"
        f"-Drop by and say hello! :speech_balloon:\n"
        f":sparkles: [Achievements](https://discord.com/channels/1272629330115297330/1272629331524587624)\n"
        f"-Show off your gains and achievements.\n"
        f":speech_balloon: [Clan Chat](https://discord.com/channels/1272629330115297330/1272875477555482666)\n"
        f"-Stay updated on what's happening in the clan.\n"
        f":bow_and_arrow: [Team Finder](https://discord.com/channels/1272629330115297330/1272648555772776529)\n"
        f"-Find teams for PVM activities.\n"
        f":loudspeaker: [Events](https://discord.com/channels/1272629330115297330/1272646577432825977)\n"
        f"-Stay informed about upcoming events, competitions, and activities!\n"
        f":crossed_swords: [Rank Up](https://discord.com/channels/1272629330115297330/1272648472184487937)\n"
        f"-Use the buttons in this channel to request a rank up.\n\n"
        f":warning: If you encounter any issues, you can always reach out to the Clan Staff or use the "
        f"[Support Ticket channel](https://discord.com/channels/1272629330115297330/1272648498554077304) for assistance."
    )

    await interaction.response.send_message(welcome_message)

# ---------------------------
# 🔹RolePanel
# ---------------------------

@tree.command(name="rolepanel", description="Post the self-role assignment panel in the designated channel.")
async def rolepanel(interaction: discord.Interaction):
    allowed_roles = {"Senior Staff", "Moderators"}
    if not any(role.name in allowed_roles for role in interaction.user.roles):
        await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
        return

    embed = discord.Embed(
        title=":crossed_swords: Self Role Assign :crossed_swords:",
        description=(
            "Select the roles for the content that you wish to be notified for. "
            "De-select to remove the role from your account."
        ),
        color=discord.Color.red()
    )
    embed.set_footer(text="Select your roles")

    guild = interaction.guild
    emoji_names = [
        "tob", "cox", "toa", "hmt", "cm", "extoa", "graardor", "sara", "zammy", "arma",
        "nex", "corp", "callisto", "vetion", "venenatis", "hueycoatl", "yama", "raffle",
        "event", "sotw", "botw", "sanguine_sunday"
    ]
    emojis = {name: discord.utils.get(guild.emojis, name=name) for name in emoji_names}

    buttons_info = [
        ("Theatre of Blood - TOB", emojis.get("tob")),
        ("Chambers of Xeric - COX", emojis.get("cox")),
        ("Tombs of Amascut - TOA", emojis.get("toa")),
        ("Theatre of Blood Hard Mode - HMT", emojis.get("hmt")),
        ("Chambers of Xeric Challenge Mode - COX CMs", emojis.get("cm")),
        ("Tombs of Amascut Expert - TOA EXP", emojis.get("extoa")),
        ("General Graardor - Bandos GWD", emojis.get("graardor")),
        ("Commander Zilyana - Saradomin GWD", emojis.get("sara")),
        ("K'ril Tsutsaroth - Zamorak GWD", emojis.get("zammy")),
        ("Kree'arra - Armadyl GWD", emojis.get("arma")),
        ("Nex", emojis.get("nex")),
        ("Corporeal Beast - Corp", emojis.get("corp")),
        ("Callisto", emojis.get("callisto")),
        ("Vet'ion", emojis.get("vetion")),
        ("Venenatis", emojis.get("venenatis")),
        ("Hueycoatl", emojis.get("hueycoatl")),
        ("Yama", emojis.get("yama")),
        ("Raffles", emojis.get("raffle")),
        ("Events", emojis.get("event")),
        ("Skill of the Week", emojis.get("sotw")),
        ("Boss of the Week", emojis.get("botw")),
        ("Sanguine Sunday", emojis.get("sanguine_sunday")),
    ]

    view = discord.ui.View(timeout=None)

    async def button_callback(interaction: discord.Interaction):
        role_name = interaction.data['custom_id']
        role = discord.utils.get(interaction.guild.roles, name=role_name)
    
        if role is None:
            await interaction.response.send_message(f"Error: Role '{role_name}' not found.", ephemeral=True)
            return
    
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            feedback = f"{interaction.user.mention}, role **{role_name}** removed."
        else:
            await interaction.user.add_roles(role)
            feedback = f"{interaction.user.mention}, role **{role_name}** added."
    
        # Send a non-ephemeral message so it can be deleted
        await interaction.response.send_message(feedback, ephemeral=False)
    
        # Wait 1 second then delete the message
        await asyncio.sleep(1)
        try:
            await interaction.delete_original_response()
        except Exception:
            pass

    for label, emoji in buttons_info:
        button = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, emoji=emoji, custom_id=label)
        button.callback = button_callback
        view.add_item(button)

    channel = interaction.guild.get_channel(1272648586198519818)
    if channel is None:
        await interaction.response.send_message("❌ Could not find the self-role channel.", ephemeral=True)
        return

    await channel.send(embed=embed, view=view)
    await interaction.response.send_message(f"✅ Role panel posted in {channel.mention}", ephemeral=True)

# ---------------------------
# Event Panel
# ---------------------------

@bot.tree.command(name="event_panel", description="Open the event panel to create BOTW or SOTW events")
async def event_panel(interaction: discord.Interaction):
    custom_emoji_skill = discord.utils.get(interaction.guild.emojis, name="skill")

    button_botw = Button(label="Boss of the Week (BOTW)", style=discord.ButtonStyle.primary, emoji="⚔️")
    button_sotw = Button(label="Skill of the Week (SOTW)", style=discord.ButtonStyle.primary, emoji=custom_emoji_skill)

    view = View(timeout=None)
    view.add_item(button_botw)
    view.add_item(button_sotw)

    async def botw_panel(inner_interaction: discord.Interaction):
        # BOTW buttons
        bosses = [
            "General Graardor", "K'ril Tsutsaroth", "Commander Zilyana", "Kree'Arra", "Nex",
            "Callisto", "Vet'ion", "Venenatis", "Chambers Of Xeric", "Tombs Of Amascut", "Theatre Of Blood",
            "Araxxor", "Vardorvis", "Duke Sucellus", "The Leviathan", "The Whisperer", "Dagannoth Kings",
            "Corporeal Beast", "Vorkath", "Zulrah", "The Gauntlet", "Phantom Muspah", "Nightmare", "Phosani", "Yama"
        ]

        view_botw = View(timeout=None)
        for boss in bosses:
            emoji_name = boss.lower().replace(" ", "_").replace("'", "").replace("-", "")
            emoji = discord.utils.get(inner_interaction.guild.emojis, name=emoji_name)
            button = Button(label=boss, style=discord.ButtonStyle.secondary, emoji=emoji)

            async def boss_callback(b_int: discord.Interaction, b_name=boss):
                event_name = b_name
                description = f"Defeat {b_name} in this week's challenge!"
                metric = METRIC_MAPPING.get(event_name, event_name.lower().replace(" ", "_"))
                await create_event(b_int, event_name, description)
                await create_wise_old_man_competition(metric, description)

            button.callback = boss_callback
            view_botw.add_item(button)

        await inner_interaction.response.edit_message(content="Select the boss for this week's event:", view=view_botw)

    async def sotw_panel(inner_interaction: discord.Interaction):
        skills = [
            "Farming", "Fishing", "Hunter", "Mining", "Woodcutting", "Cooking", "Crafting",
            "Fletching", "Herblore", "Runecrafting", "Smithing", "Agility", "Construction", "Firemaking", "Slayer", "Thieving"
        ]

        view_sotw = View(timeout=None)
        for skill in skills:
            emoji_name = skill.lower().replace(" ", "_")
            emoji = discord.utils.get(inner_interaction.guild.emojis, name=emoji_name)
            button = Button(label=skill, style=discord.ButtonStyle.secondary, emoji=emoji)

            async def skill_callback(s_int: discord.Interaction, s_name=skill):
                event_name = s_name
                description = f"Master {s_name} in this week's skill challenge!"
                metric = METRIC_MAPPING.get(event_name, event_name.lower().replace(" ", "_"))
                await create_event(s_int, event_name, description)
                await create_wise_old_man_competition(metric, description)

            button.callback = skill_callback
            view_sotw.add_item(button)

        await inner_interaction.response.edit_message(content="Select the skill for this week's event:", view=view_sotw)

    button_botw.callback = botw_panel
    button_sotw.callback = sotw_panel

    await interaction.response.send_message("Click a button to create an event:", view=view, ephemeral=False)

# ---------------------------
# 🔹 RSN Commands
# ---------------------------
rsn_write_queue = asyncio.Queue()

async def rsn_writer():
    while True:
        member_id, rsn_value = await rsn_write_queue.get()
        try:
            cell = rsn_sheet.find(member_id)
            if cell is not None:
                rsn_sheet.update_cell(cell.row, 2, rsn_value)
            else:
                rsn_sheet.append_row([member_id, rsn_value])
        except Exception as e:
            print(f"Error writing RSN to sheet: {e}")
        rsn_write_queue.task_done()

@tree.command(name="rsn_panel", description="Open the RSN registration panel.")
@app_commands.checks.has_any_role("Moderators")
async def rsn_panel(interaction: discord.Interaction):
    class RSNModal(discord.ui.Modal, title="Register your RuneScape Name"):
        rsn = discord.ui.TextInput(
            label="Enter your RSN",
            placeholder="e.g. Zezima",
            required=True,
            max_length=12
        )

        async def on_submit(self, interaction: discord.Interaction):
            member_id = str(interaction.user.id)
            rsn_value = self.rsn.value
            rsn_write_queue.put_nowait((member_id, rsn_value))
            await interaction.response.send_message(
                f"✅ Your RSN has been registered as **{rsn_value}**.",
                ephemeral=True
            )

    view = discord.ui.View()
    button = discord.ui.Button(label="Register RSN", style=discord.ButtonStyle.primary)

    async def button_callback(interaction2: discord.Interaction):
        await interaction2.response.send_modal(RSNModal())

    button.callback = button_callback
    view.add_item(button)

    await interaction.response.send_message(
        "📝 Click below to register your RuneScape Name:",
        view=view,
        ephemeral=True
    )


@tree.command(name="rsn", description="Check your registered RSN.")
async def rsn(interaction: discord.Interaction):
    member_id = str(interaction.user.id)

    try:
        cell = rsn_sheet.find(member_id)
        rsn_value = rsn_sheet.cell(cell.row, 2).value
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
# 🔹 On Ready
# ---------------------------
@bot.event
async def on_ready():
    bot.loop.create_task(rsn_writer())
    print(f"✅ Logged in as {bot.user}")
    synced = await tree.sync()
    print(f"✅ Synced {len(synced)} slash commands.")

bot.run(os.getenv('DISCORD_BOT_TOKEN'))
