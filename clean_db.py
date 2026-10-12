import asyncio
import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "dashboard", ".env.local"))


async def clean_database():
    uri = os.getenv("MONGO_URI")
    if not uri:
        print("Error: MONGO_URI not found in .env")
        return

    print("Connecting to MongoDB...")
    client = AsyncIOMotorClient(uri)
    db = client.giveaway_bot

    # Drop the collection
    await db.stock.drop()
    print("[SUCCESS] Successfully dropped the 'stock' collection in 'giveaway_bot' database.")
    print("The database is now completely clean and ready for the Giveaway bot.")


if __name__ == "__main__":
    asyncio.run(clean_database())
