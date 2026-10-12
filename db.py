import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument
from datetime import UTC

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client.giveaway_bot
stock_col = db.stock
settings_col = db.settings
logs_col = db.activity_logs


async def add_stock(country: str, email: str, plan: str, payment: str, cookies: str, password: str = None):
    """Adds a new valid account to the stock collection."""
    if email == "Unknown":
        import uuid

        email = f"Unknown_{uuid.uuid4().hex}"

    std_plan = standardize_plan(plan)

    await stock_col.update_one(
        {"email": email},
        {
            "$set": {
                "country": country,
                "email": email,
                "plan": plan,
                "standard_plan": std_plan,
                "payment": payment,
                "cookies": cookies,
                "password": password,
                "status": "active",
            }
        },
        upsert=True,
    )


async def get_stock_counts() -> dict:
    """Returns a dictionary of active stock counts by country."""
    pipeline = [{"$match": {"status": "active"}}, {"$group": {"_id": "$country", "count": {"$sum": 1}}}]
    cursor = stock_col.aggregate(pipeline)
    counts = {}
    async for doc in cursor:
        counts[doc["_id"]] = doc["count"]
    return counts


async def get_total_stock_count(country: str) -> int:
    """Returns the total active stock for a specific country."""
    return await stock_col.count_documents({"status": "active", "country": country})


async def get_overall_plan_counts() -> dict:
    """Returns counts of standard plans across all active stock."""
    pipeline = [{"$match": {"status": "active"}}, {"$group": {"_id": "$standard_plan", "count": {"$sum": 1}}}]
    cursor = stock_col.aggregate(pipeline)
    counts = {}
    async for doc in cursor:
        plan_name = doc["_id"] or "Unknown"
        counts[plan_name] = doc["count"]
    return counts


async def get_all_active_stock_list() -> list:
    """Returns all active stock items as a list of dictionaries."""
    cursor = stock_col.find({"status": "active"})
    return await cursor.to_list(length=100000)


async def get_random_active_stock():
    """Fetches a random active cookie from the stock to give away."""
    pipeline = [{"$match": {"status": "active"}}, {"$sample": {"size": 1}}]
    cursor = stock_col.aggregate(pipeline)
    async for doc in cursor:
        return doc
    return None


async def get_all_active_stock():
    """Returns a cursor of all active stock for the 24h background checker."""
    return stock_col.find({"status": "active"})


async def remove_stock(email: str):
    """Removes a cookie from active stock (used when it dies or gets given away)."""
    await stock_col.delete_one({"email": email})


def standardize_plan(raw_plan: str) -> str:
    """Translates localized Netflix plans to a standard English equivalent."""
    if not raw_plan or raw_plan == "N/A":
        return "Premium"

    p = raw_plan.lower()
    if any(x in p for x in ["error", "500", "server error"]):
        return "Premium"
    elif any(x in p for x in ["premium", "prémium", "pre", "4k", "ultra"]):
        return "Premium"
    elif any(x in p for x in ["standard", "estándar", "padrão", "standart", "hd", "1080"]):
        return "Standard"
    elif any(x in p for x in ["basic", "básico", "basique", "basico", "720"]):
        return "Basic"
    elif any(x in p for x in ["mobile", "móvil", "mobil"]):
        return "Mobile"
    return "Premium"


async def get_plans_for_country(country: str) -> dict:
    """Returns a dict of standard plan counts for a given country."""
    cursor = stock_col.find({"status": "active", "country": country})
    plan_counts = {"Premium": 0, "Standard": 0, "Basic": 0, "Mobile": 0, "N/A": 0}

    async for doc in cursor:
        p = doc.get("standard_plan")
        if not p:
            p = standardize_plan(doc.get("plan", ""))

        if p in plan_counts:
            plan_counts[p] += 1
        else:
            plan_counts["N/A"] += 1

    # Filter out zeros for cleaner UI
    return {k: v for k, v in plan_counts.items() if v > 0}


async def get_specific_stock(country: str, standard_plan: str):
    """Fetches a specific stock matching the country and standard plan."""
    pipeline = [
        {
            "$match": {
                "status": "active",
                "country": country,
                "$or": [{"standard_plan": standard_plan}, {"plan": {"$regex": standard_plan, "$options": "i"}}],
            }
        },
        {"$sample": {"size": 1}},
    ]
    cursor = stock_col.aggregate(pipeline)
    async for doc in cursor:
        return doc
    return None


async def get_any_stock_by_plan(standard_plan: str):
    """Fetches any stock matching the standard plan regardless of country."""
    pipeline = [
        {
            "$match": {
                "status": "active",
                "$or": [{"standard_plan": standard_plan}, {"plan": {"$regex": standard_plan, "$options": "i"}}],
            }
        },
        {"$sample": {"size": 1}},
    ]
    cursor = stock_col.aggregate(pipeline)
    async for doc in cursor:
        return doc
    return None


async def get_settings() -> dict:
    """Fetches the current settings from DB, creates default if not exists."""
    settings = await settings_col.find_one_and_update(
        {"_id": "config"},
        {
            "$setOnInsert": {
                "channels": [],
                "drop_interval_minutes": 120,
                "drops_per_day": 3,
                "drops_today": 0,
                "last_drop_time": None,
            }
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return settings


async def update_settings(update_dict: dict):
    """Updates the settings document."""
    await settings_col.update_one({"_id": "config"}, {"$set": update_dict}, upsert=True)


async def log_activity(action: str, details: str = "", status: str = "success"):
    """Logs an activity event in MongoDB for dashboard tracking."""
    from datetime import datetime

    try:
        await logs_col.insert_one(
            {"action": action, "details": details, "status": status, "timestamp": datetime.now(UTC)}
        )
    except Exception:
        pass


async def get_recent_activities(limit: int = 20) -> list:
    """Fetches recent activity logs."""
    try:
        cursor = logs_col.find().sort("timestamp", -1).limit(limit)
        activities = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            if "timestamp" in doc and doc["timestamp"]:
                doc["timestamp"] = doc["timestamp"].isoformat()
            activities.append(doc)
        return activities
    except Exception:
        return []
