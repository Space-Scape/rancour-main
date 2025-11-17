import discord
from discord.ext import commands
import os

# --- CONFIGURATION ---
# The script will now pull the token from your environment variables
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = 1272629330115297330 # The ID of the server with duplicate commands
# ---------------------

if not BOT_TOKEN:
    print("❌ DISCORD_BOT_TOKEN environment variable not set. Cannot start.")
    exit()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} to clear commands...")

    # This is the target guild
    target_guild = discord.Object(id=GUILD_ID)

    try:
        # Clear commands specifically for the target guild
        print(f"Clearing commands for guild: {GUILD_ID}...")
        bot.tree.clear_commands(guild=target_guild)
        await bot.tree.sync(guild=target_guild)
        print("✅ Guild-specific commands cleared.")

        # Also clear any global commands
        # This ensures a completely clean slate
        print("Clearing global commands...")
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync(guild=None)
        print("✅ Global commands cleared.")

    except Exception as e:
        print(f"An error occurred during clearing: {e}")
    finally:
        print("\n---")
        print("✅ Task complete. You can now STOP this script.")
        print("Run your main bot file to re-register the commands correctly.")
        print("---\n")
        await bot.close()

bot.run(BOT_TOKEN)
