#!/usr/bin/env python3
"""
Warhammer 40K Army Randomiser - Discord Bot
"""

import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()


class ArmyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.load_extension("cogs.army")
        await self.tree.sync()

    async def on_ready(self):
        print(f"Logged in as {self.user}")


bot = ArmyBot()


@bot.tree.command(name="reload", description="Reload the bot commands (hot reload)")
async def reload_commands(interaction: discord.Interaction):
    try:
        await bot.reload_extension("cogs.army")
        await bot.tree.sync()
        await interaction.response.send_message("Reloaded successfully!", ephemeral=True)
    except Exception as error:
        await interaction.response.send_message(f"Reload failed: {error}", ephemeral=True)


if __name__ == "__main__":
    discord_token = os.getenv("DISCORD_TOKEN")
    if not discord_token:
        print("Error: DISCORD_TOKEN not found in .env file")
        exit(1)
    bot.run(discord_token)
