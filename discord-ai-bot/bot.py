import os
import sys
import traceback

import discord
from discord import app_commands
from dotenv import load_dotenv

import ai_handler
import formatter

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

missing = [name for name, val in [("DISCORD_TOKEN", DISCORD_TOKEN), ("GEMINI_API_KEY", GEMINI_API_KEY)] if not val]
if missing:
    for name in missing:
        print(f"ERROR: Missing required environment variable: {name}", file=sys.stderr)
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)


@bot.event
async def on_ready():
    """Print a confirmation message when the bot connects to Discord."""
    print(f"Logged in as {bot.user}")


@tree.command(name="ai", description="Send a prompt to the AI and get a reply.")
@app_commands.describe(prompt="Your message to the AI")
async def ai_command(interaction: discord.Interaction, prompt: str):
    """Handle the /ai slash command by forwarding the prompt to Gemini and returning the response."""
    await interaction.response.defer()

    try:
        text = await ai_handler.get_response(interaction.user.id, prompt)
    except Exception:
        traceback.print_exc(file=sys.stderr)
        await interaction.followup.send("Something went wrong. Please try again.")
        return

    chunks = formatter.split_message(text)
    await interaction.followup.send(chunks[0])
    for chunk in chunks[1:]:
        await interaction.followup.send(chunk)


@tree.command(name="ai-clear", description="Wipe your conversation history and start fresh.")
async def ai_clear_command(interaction: discord.Interaction):
    """Handle the /ai-clear slash command by erasing the user's conversation history."""
    ai_handler.clear_history(interaction.user.id)
    await interaction.response.send_message("History cleared.", ephemeral=True)


async def main():
    """Start the bot, sync slash commands, and connect to Discord."""
    async with bot:
        await bot.tree.sync()
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
