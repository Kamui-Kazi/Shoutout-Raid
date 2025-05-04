import os
from dotenv import load_dotenv
import asyncio
import logging
import asqlite

from shout_bot import ShoutBot

import twitchio

LOGGER: logging.Logger = logging.getLogger("Bot hub")

def main(auth_mode:bool = False) -> None:
    load_dotenv()
    twitchio.utils.setup_logging(level=logging.INFO)
    
    async def runner() -> None:
        async with asqlite.create_pool("tokens.db") as tdb, ShoutBot(auth_mode=auth_mode, token_database=tdb) as sbot:
            await sbot.setup_database()
            await sbot.start()
            
    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        LOGGER.warning("Shutting down due to KeyboardInterrupt...")