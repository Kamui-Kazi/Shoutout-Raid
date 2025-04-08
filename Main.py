import os
from dotenv import load_dotenv
from my_websockets import my_websockets
import logging
import twitchio


LOGGER: logging.Logger = logging.getLogger(__name__)
twitchio.utils.setup_logging(level=logging.INFO)


def main() -> None:
    load_dotenv()
    ws = my_websockets()
    ws.test()
    ws.close()

    # async def runner() -> None:
    #     # async with asqlite.create_pool("tokens.db") as tdb, Bot(token_database=tdb) as bot:
    #     #     await bot.setup_database()
    #     #     await bot.start()
    #     pass

    # try:
    #     asyncio.run(runner())
    # except KeyboardInterrupt:
    #     LOGGER.warning("Shutting down due to KeyboardInterrupt...")


if __name__ == "__main__":
    main()