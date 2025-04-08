import os
from dotenv import load_dotenv
import logging

from my_websockets import my_websockets



LOGGER: logging.Logger = logging.getLogger("WS")







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