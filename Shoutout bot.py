import creds
import asyncio
import logging
import asqlite
import twitchio
import time
from twitchio.ext import commands
from twitchio import eventsub
from twitchio import utils

LOGGER: logging.Logger = logging.getLogger("Bot")

# Replace with your bot's credentials
CLIENT_ID = creds.client_id
CLIENT_SECRET = creds.client_secret
BROADCASTER_ID = creds.target_id  # Broadcaster's twitch user ID
#BROADCASTER_ID = creds.owner_id  # My twitch user ID (for testing)
OWNER_ID = creds.owner_id
ACCESS_TOKEN = creds.oauth_token
REFRESH_TOKEN = creds.oauth_refresh


#making the bot
class RaidBot(commands.Bot):
    def __init__(self, *, token_database: asqlite.Pool):
        self.token_database = token_database
        super().__init__(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            bot_id=OWNER_ID,  # Set to main account ID
            owner_id=OWNER_ID,  # Set to main account ID
            
            prefix="!",
        )
    
        
    async def setup_hook(self):
        await self.add_component(RaidComponent(self))

        # Subscribe to raid events
        subscription = eventsub.ChannelRaidSubscription(to_broadcaster_user_id=BROADCASTER_ID)
        await self.subscribe_websocket(payload=subscription)

    async def add_token(self, token: str, refresh: str) -> twitchio.authentication.ValidateTokenPayload:
        """Add the OAuth token and refresh token"""
        resp: twitchio.authentication.ValidateTokenPayload = await super().add_token(token, refresh)

        # Store tokens in the SQLite database
        query = """
        INSERT INTO tokens (user_id, token, refresh)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            token = excluded.token,
            refresh = excluded.refresh;
        """
        async with self.token_database.acquire() as connection:
            await connection.execute(query, (resp.user_id, token, refresh))

        LOGGER.info("Added token to the database for user: %s", resp.user_id)
        return resp

    async def load_tokens(self) -> None:
        """Load tokens from the SQLite database"""
        async with self.token_database.acquire() as connection:
            rows = await connection.fetchall("SELECT * FROM tokens")

        for row in rows:
            await self.add_token(row["token"], row["refresh"])

    async def setup_database(self) -> None:
        """Create tokens table in the SQLite database if not exists"""
        query = """CREATE TABLE IF NOT EXISTS tokens(user_id TEXT PRIMARY KEY, token TEXT NOT NULL, refresh TEXT NOT NULL)"""
        async with self.token_database.acquire() as connection:
            await connection.execute(query)

    async def event_ready(self) -> None:
        """When the bot is ready"""
        LOGGER.info("Successfully logged in as: %s", self.bot_id)

#creating eventsub connection and manager
class RaidComponent(commands.Component):
    def __init__(self, bot: RaidBot):
        self.bot = bot

    @commands.Component.listener()
    async def event_raid(self, payload: twitchio.ChannelRaid) -> None:
        """Triggered when a raid occurs from another channel."""
    
        # Extracting raider information
        raider_name = payload.from_broadcaster
        num_raiders = payload.viewer_count
        
        # Log the raid information
        LOGGER.info(f"Raid detected from {raider_name} with {num_raiders} viewers!")
        
        # Send a message in the broadcaster's channel
        await payload.to_broadcaster.send_shoutout(
            to_broadcaster=raider_name,
            moderator = self.bot.bot_id
        )
        await time.sleep(1)
        await payload.to_broadcaster.send_message(
            sender=self.bot.bot_id,
            message="!raiders"
        )

def main():
    utils.setup_logging(level=logging.INFO)

    async def runner():
        async with asqlite.create_pool("tokens.db") as tdb, RaidBot(token_database=tdb) as bot:
            await bot.setup_database()
            await bot.start()

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Shutting down...")

if __name__ == "__main__":
    main()