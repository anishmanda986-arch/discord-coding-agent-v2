"""Production Discord gateway adapter for the agent core.

The business logic remains in MessageEventHandler so the web console and Discord
use the same command and intent pipeline.
"""
import os
from typing import Optional

from .commands import BotCommandsHandler
from .handlers import MessageEventHandler
from ..storage.db import Database
from ..config import config


class DiscordCodingAgentBot:
    def __init__(self, db_path: Optional[str] = None):
        self.db = Database(db_path or config.database_path)
        self.commands_handler = BotCommandsHandler(self.db)
        self.message_handler = MessageEventHandler(self.db)
        self.discord_client = None

    async def initialize(self):
        return True

    async def simulate_user_prompt(self, channel_id: str, user_id: str, prompt: str, callback=None):
        return await self.message_handler.handle_user_message(
            channel_id=channel_id, user_id=user_id, content=prompt,
            send_embed_callback=callback, send_text_callback=callback
        )

    def build_discord_client(self):
        """Create the real discord.py client and register every supported command."""
        try:
            import discord
            from discord import app_commands
        except ImportError as exc:
            raise RuntimeError("discord.py is required to run the Discord gateway") from exc

        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.messages = True
        bot = discord.Client(intents=intents)
        tree = app_commands.CommandTree(bot)
        self.discord_client = bot

        async def run_text(interaction, content: str):
            await interaction.response.defer(thinking=True)
            async def send_text(text):
                await interaction.followup.send(text[:1900])
            async def send_embed(data):
                embed = discord.Embed(title=data.get("title", "Coding Agent"), description=str(data.get("description", ""))[:4000], color=data.get("color", 0x5865F2))
                await interaction.followup.send(embed=embed)
            async def send_file(path):
                await interaction.followup.send(file=discord.File(path))
            return await self.message_handler.handle_user_message(
                str(interaction.channel_id), str(interaction.user.id), content,
                guild_id=str(interaction.guild_id) if interaction.guild_id else None,
                send_embed_callback=send_embed, send_file_callback=send_file,
                send_text_callback=send_text)

        @bot.event
        async def on_ready():
            await tree.sync()
            print(f"Discord bot connected as {bot.user} with {len(tree.get_commands())} slash commands")

        @bot.event
        async def on_message(message):
            if message.author.bot:
                return
            # Natural messages and legacy text commands share the same core handler.
            async def send_text(text): await message.channel.send(text[:1900])
            async def send_embed(data):
                e = discord.Embed(title=data.get("title", "Coding Agent"), description=str(data.get("description", ""))[:4000], color=data.get("color", 0x5865F2))
                await message.channel.send(embed=e)
            async def send_file(path): await message.channel.send(file=discord.File(path))
            await self.message_handler.handle_user_message(
                str(message.channel.id), str(message.author.id), message.content,
                guild_id=str(message.guild.id) if message.guild else None,
                send_embed_callback=send_embed, send_file_callback=send_file,
                send_text_callback=send_text)

        @tree.command(name="models", description="Discover available AI models")
        @app_commands.describe(query="Optional model search filter")
        async def models(interaction: discord.Interaction, query: Optional[str] = None):
            await run_text(interaction, "/models" + (f" {query}" if query else ""))

        @tree.command(name="model", description="Alias for models")
        async def model(interaction: discord.Interaction, query: Optional[str] = None):
            await run_text(interaction, "/models" + (f" {query}" if query else ""))

        @tree.command(name="modle", description="Compatibility alias for models")
        async def modle(interaction: discord.Interaction, query: Optional[str] = None):
            await run_text(interaction, "/models" + (f" {query}" if query else ""))

        @tree.command(name="token", description="Show token usage and quota")
        @app_commands.describe(admin="Request admin diagnostics (requires ADMIN_USER_IDS)")
        async def token(interaction: discord.Interaction, admin: bool = False):
            await run_text(interaction, "/token" + (" --admin" if admin else ""))

        @tree.command(name="switch", description="Switch model or fallback routing")
        async def switch(interaction: discord.Interaction, model_name: Optional[str] = None, auto: Optional[bool] = None):
            args = "/switch" + (f" {model_name}" if model_name else "") + (" on" if auto is True else " off" if auto is False else "")
            await run_text(interaction, args)

        @tree.command(name="test", description="Run system diagnostics or project tests")
        async def test(interaction: discord.Interaction): await run_text(interaction, "/test")

        @tree.command(name="api", description="Configure an OpenAI-compatible API")
        async def api(interaction: discord.Interaction, provider: str = "OpenRouter", base_url: str = "https://openrouter.ai/api/v1", api_key: str = ""):
            await run_text(interaction, f"/api {provider} {base_url} {api_key}")

        @tree.command(name="connect", description="Register an agent gateway")
        async def connect(interaction: discord.Interaction, agent_id: str = "coding_agent_primary", endpoint: str = ""):
            await run_text(interaction, f"/connect {agent_id} {endpoint or 'http://127.0.0.1:3000'}")

        @tree.command(name="disable", description="Toggle this channel")
        async def disable(interaction: discord.Interaction): await run_text(interaction, "/disable")
        return bot

    def run(self):
        if not config.discord_token:
            raise RuntimeError("DISCORD_BOT_TOKEN is not configured")
        self.build_discord_client().run(config.discord_token)
