"""Production entrypoint for the Discord Coding Agent."""
from dotenv import load_dotenv
load_dotenv()

from app.bot.client import DiscordCodingAgentBot

if __name__ == "__main__":
    DiscordCodingAgentBot().run()
