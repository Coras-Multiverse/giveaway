import asyncio
import logging
import os

import db
import utils

# Disable all the noisy logs from scraper and httpx
logging.getLogger().setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("scraper").setLevel(logging.CRITICAL)


async def import_output():
    output_dir = "output"
    if not os.path.exists(output_dir):
        print("Output directory not found!")
        return

    countries = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d))]
    print(f"📦 Found {len(countries)} countries in output folder.\n")

    total_added = 0
    total_failed = 0

    for country in countries:
        country_dir = os.path.join(output_dir, country)
        cookie_file = os.path.join(country_dir, "cookies.txt")

        if not os.path.exists(cookie_file):
            continue

        with open(cookie_file, encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # The output format separates accounts with 'Valid Cookie / Every day!' or similar text
        # Let's split by 'Valid Cookie'
        items = content.split("Valid Cookie")

        # We don't need split_cookie_text since we are splitting by the known delimiter
        valid_items = [i for i in items if "netflix.com" in i.lower()]

        if not valid_items:
            continue

        print(f"▶️ Processing {len(valid_items)} items for {country}...")

        for item in valid_items:
            result = await utils.process_raw_item(item)
            if result:
                await db.add_stock(
                    country=result["country"],
                    email=result["email"],
                    plan=result["plan"],
                    payment=result["payment"],
                    cookies=result["cookies"],
                )
                total_added += 1
                print(f"   ✅ Added: {result['email']} | {result['plan']} | {result['country']}")
            else:
                total_failed += 1
                # print(f"   ❌ Failed / Dead Cookie")

    print("\n" + "=" * 30)
    print("🎉 IMPORT COMPLETE 🎉")
    print(f"✅ Total Valid Added: {total_added}")
    print(f"❌ Total Dead/Failed: {total_failed}")
    print("=" * 30)


if __name__ == "__main__":
    asyncio.run(import_output())
