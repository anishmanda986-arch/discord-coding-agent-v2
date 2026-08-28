import os
import asyncio
from typing import Optional

from .commands import BotCommandsHandler
from .handlers import MessageEventHandler
from .embeds import DiscordEmbedFormatter
from ..storage.db import Database
from ..config import config

class DiscordCodingAgentBot:
    """
    Production Discord Bot client wrapper.
    Supports discord.py integration and programmatic headless simulation.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db = Database(db_path or config.database_path)
        self.commands_handler = BotCommandsHandler(self.db)
        self.message_handler = MessageEventHandler(self.db)

    async def initialize(self):
        """Pre-warms database and skills registry."""
        pass

    async def simulate_user_prompt(self, channel_id: str, user_id: str, prompt: str, callback=None):
        """Simulates conversational turn for testing and web console execution."""
        return await self.message_handler.handle_user_message(
            channel_id=channel_id,
            user_id=user_id,
            content=prompt,
            send_embed_callback=callback
        )
