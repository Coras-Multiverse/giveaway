import asyncio
import sys

# Ensure unicode output on windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import db
import utils


async def fix_unknown_stock():
    print("Fetching stock with 'Unknown' country...")
    cursor = db.stock_col.find({"country": "Unknown"})
    stocks = await cursor.to_list(length=None)

    total = len(stocks)
    print(f"Found {total} items to fix.")

    working = 0
    dead = 0

    for i, s in enumerate(stocks, 1):
        email = s["email"]
        cookies_str = s["cookies"]
        cookies_list = utils.parse_netflix_cookies(cookies_str)

        print(f"[{i}/{total}] Checking {email}...", end=" ", flush=True)

        if not cookies_list:
            print("❌ Dead (Invalid Cookie JSON). Deleting.")
            await db.stock_col.delete_one({"email": email})
            dead += 1
            continue

        try:
            info = await utils.scraper.fetch_enhanced_account_details(cookies_list)

            # if info is None or plan is missing, it's dead
            if not info or info.get("plan") in ["N/A", "None", "", None]:
                print("❌ Dead (Subscription expired or login failed). Deleting.")
                await db.stock_col.delete_one({"email": email})
                dead += 1
            else:
                country = info.get("country", "Unknown")
                if country != "Unknown" and country != "N/A":
                    await db.stock_col.update_one(
                        {"email": email}, {"$set": {"country": country, "plan": info.get("plan")}}
                    )
                    print(f"✅ Working! Updated to Country: {country}, Plan: {info.get('plan')}")
                else:
                    # Still unknown, but working.
                    await db.stock_col.update_one({"email": email}, {"$set": {"plan": info.get("plan")}})
                    print(f"✅ Working! But country still Unknown/N/A. Plan: {info.get('plan')}")
                working += 1

        except Exception as e:
            print(f"⚠️ Error checking {email}: {e}. Skipping deletion for now.")

        # Cooldown between checks
        await asyncio.sleep(4)

    print("\n--- Scan Complete ---")
    print(f"Total Processed: {total}")
    print(f"✅ Working (Kept): {working}")
    print(f"❌ Dead (Deleted): {dead}")


if __name__ == "__main__":
    asyncio.run(fix_unknown_stock())
