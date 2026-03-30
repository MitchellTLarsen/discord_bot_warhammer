#!/usr/bin/env python3
"""
Warhammer 40K Army Randomiser - Discord Bot
"""

import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# Dev mode: commands only sync to this guild (instant updates, isolated from prod)
DEV_GUILD_ID = os.getenv("DEV_GUILD_ID")
DEV_GUILD = discord.Object(id=int(DEV_GUILD_ID)) if DEV_GUILD_ID else None


class ArmyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.load_extension("cogs.army")
        if DEV_GUILD:
            # Dev mode: sync to test server only (instant, isolated)
            self.tree.copy_global_to(guild=DEV_GUILD)
            await self.tree.sync(guild=DEV_GUILD)
            print(f"[DEV MODE] Commands synced to guild {DEV_GUILD_ID}")
        else:
            # Production: sync globally
            await self.tree.sync()

    async def on_ready(self):
        mode = "DEV" if DEV_GUILD else "PROD"
        print(f"[{mode}] Logged in as {self.user}")


bot = ArmyBot()


@bot.tree.command(name="reload", description="Reload the bot commands (hot reload)")
async def reload_commands(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        await bot.reload_extension("cogs.army")
        if DEV_GUILD:
            bot.tree.copy_global_to(guild=DEV_GUILD)
            await bot.tree.sync(guild=DEV_GUILD)
        else:
            await bot.tree.sync()
        await interaction.followup.send("Reloaded successfully!")
    except Exception as error:
        await interaction.followup.send(f"Reload failed: {error}")


if __name__ == "__main__":
    discord_token = os.getenv("DISCORD_TOKEN")
    if not discord_token:
        print("Error: DISCORD_TOKEN not found in .env file")
        exit(1)
    bot.run(discord_token)
