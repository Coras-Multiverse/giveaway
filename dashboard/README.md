# ⚡ Giveaway Pro - Vercel Command Center & Admin Hub

Enterprise-grade Control Panel & Automation Hub for Telegram Giveaway Bot & Account Checkers. Fully deployable on **Vercel** with zero-configuration serverless architecture.

---

## 🌟 Key Features

1. **Dashboard Mission Control**
   - Live KPI overview (Total stock, active stock, given away, dead stock).
   - Real-time country distribution progress bars with country count.
   - Subscription plan breakdown (Premium 4K, Standard HD, Basic, Mobile).
   - Telegram Bot live connection status & username badge.
   - 1-Click Instant Giveaway Drop trigger.
   - Live operational audit logs timeline.

2. **Full Stock Management Inventory**
   - Search by email, country, or plan.
   - Filter by status (Active, Given Away, Dead).
   - Filter by Subscription Plan (Premium, Standard, Basic, Mobile).
   - Add Single Stock Modal with automatic plan standardization.
   - Bulk Importer for Netscape cookies, JSON arrays, and Email:Pass combos.
   - Bulk Delete and Export as JSON.
   - 1-Click cookie clipboard copy.

3. **Giveaway Automation & Instant Drops**
   - Instant drop launcher targeting all channels or a specific channel.
   - Filter by country and plan before dropping.
   - Custom broadcast message template with dynamic variables: `{country}`, `{plan}`, `{payment}`, `{email}`.
   - Auto-Drop scheduler settings: Drop interval (in minutes), max drops per day, daily counter reset.
   - Channel Manager: Add and remove Telegram broadcast channels (@handle or -100 ID).

4. **Multi-Service Live Checker Studio**
   - Live Netflix Cookie / Token validator.
   - Live Crunchyroll Authentication validator.
   - Interactive terminal output log with color-coded tags (`[HIT]`, `[BAD]`, `[ERROR]`).
   - 1-Click "Save to Stock" button for valid hits.

5. **Database Maintenance & Purge Center**
   - 1-Click Dead Stock Purge (removes all expired accounts).
   - 1-Click Given Away Account cleaner.
   - Export complete database backup as JSON.
   - MongoDB document statistics.

---

## 🚀 1-Click Deployment to Vercel

### Step 1: Import to Vercel
1. Push your repository to GitHub.
2. Go to [Vercel](https://vercel.com) and click **"Add New Project"**.
3. Import your repository.
4. Set **Root Directory** to `dashboard`.

### Step 2: Environment Variables
Add the following Environment Variables in your Vercel Project Settings:

| Variable | Description | Example |
| :--- | :--- | :--- |
| `MONGO_URI` | MongoDB Atlas Connection String | `mongodb+srv://user:pass@cluster.mongodb.net/giveaway_bot` |
| `BOT_TOKEN` | Telegram Bot Token from @BotFather | `123456789:ABCDefGhIJKlmNoPQRs...` |
| `OWNER_ID` | Telegram Numeric User ID | `123456789` |
| `CHANNEL_IDS` | Telegram Channels (comma-separated) | `@MyChannel,-1001234567890` |

### Step 3: Deploy
Click **Deploy**! Your dashboard will be live on a `.vercel.app` URL with full control!

---

## 💻 Running Locally

```bash
cd dashboard
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.
