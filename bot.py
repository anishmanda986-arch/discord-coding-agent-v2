"""Production entrypoint for the Discord Coding Agent."""
# Railway and production runners inject environment variables directly.
from app.bot.client import DiscordCodingAgentBot

if __name__ == "__main__":
    DiscordCodingAgentBot().run()
