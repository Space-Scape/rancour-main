import os
import discord
from discord.ext import commands
from discord import app_commands
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from datetime import datetime, timezone

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
    "Varlamore": ["Sulphur blades"],
    "Misthalin/wilderness": ["Zombie helm", "Zombie axe", "Dragon limbs", "Dragon metal lump"],
    "Kourend/Kebos": ["Pyromancer garb", "Pyromancer robe", "Pyromancer boots", "Tome of fire (empty)", "Phoenix", "Dragon axe", "Pyromancer hood", "Bruma torch", "Golden tench", "Warm gloves"],
    "Desert": ["Kq head", "Pharaoh's sceptre (uncharged)", "500 toa kit", "Abyssal needle", "Abyssal lantern", "Abyssal red dye", "Abyssal green dye", "Abyssal blue dye"],
    "Asgarnia": ["Dragon boots"],
    "Morytania": ["Zealot’s helm", "Zealot’s robe top", "Zealot’s robe bottom", "Zealot’s boots"],
    "Tirannwn/fremennik": ["Brine saber"],
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
        super().__init__(label="◀️ Previous", style=discord.ButtonStyle.secondary)
        self.submitting_user = submitting_user
        self.target_user = target_user
        self.screenshot = screenshot
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=BossView(self.submitting_user, self.target_user, self.screenshot, self.page - 1))

class NextPageButton(discord.ui.Button):
    def __init__(self, submitting_user, target_user, screenshot, page):
        super().__init__(label="Next ▶️", style=discord.ButtonStyle.secondary)
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
# 🔹 On Ready
# ---------------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    synced = await tree.sync()
    print(f"✅ Synced {len(synced)} slash commands.")

bot.run(os.getenv('DISCORD_BOT_TOKEN'))
