import { NextResponse } from "next/server";
import { getDatabase } from "@/lib/mongodb";
import { getBotMe } from "@/lib/telegram";
import { getFullCountryName } from "@/lib/countries";
import { standardizePlan } from "@/lib/plans";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const db = await getDatabase();
    const stockCol = db.collection("stock");
    const settingsCol = db.collection("settings");
    const logsCol = db.collection("activity_logs");

    // Total and status counts
    const totalStock = await stockCol.countDocuments({});
    const activeStock = await stockCol.countDocuments({ status: "active" });
    const usedStock = await stockCol.countDocuments({ status: "given" });
    const deadStock = await stockCol.countDocuments({ status: "dead" });

    // Country Breakdown
    const countryAgg = await stockCol
      .aggregate([
        { $match: { status: "active" } },
        { $group: { _id: "$country", count: { $sum: 1 } } },
        { $sort: { count: -1 } },
      ])
      .toArray();

    const countryMapCounts = {};
    for (const item of countryAgg) {
      const fullName = getFullCountryName(item._id);
      countryMapCounts[fullName] = (countryMapCounts[fullName] || 0) + item.count;
    }

    const countryBreakdown = Object.entries(countryMapCounts)
      .map(([country, count]) => ({ country, count }))
      .sort((a, b) => b.count - a.count);

    // Plan Breakdown
    const planAgg = await stockCol
      .aggregate([
        { $match: { status: "active" } },
        {
          $group: {
            _id: { $ifNull: ["$standard_plan", "$plan"] },
            count: { $sum: 1 },
          },
        },
      ])
      .toArray();

    const planMapCounts = {};
    for (const item of planAgg) {
      const clean = standardizePlan(item._id);
      planMapCounts[clean] = (planMapCounts[clean] || 0) + item.count;
    }

    const planBreakdown = Object.entries(planMapCounts)
      .map(([plan, count]) => ({ plan, count }))
      .sort((a, b) => b.count - a.count);

    // Settings
    const settings = (await settingsCol.findOne({ _id: "config" })) || {
      channels: [],
      drop_interval_minutes: 120,
      drops_per_day: 3,
      drops_today: 0,
      last_drop_time: null,
    };

    // Recent Activity Logs
    const recentLogs = await logsCol.find({}).sort({ timestamp: -1 }).limit(10).toArray();

    // Bot connection check
    const botInfo = await getBotMe();

    return NextResponse.json({
      success: true,
      stats: {
        totalStock,
        activeStock,
        usedStock,
        deadStock,
        countryBreakdown,
        planBreakdown,
        settings,
        recentLogs,
        botStatus: botInfo.ok ? "online" : "offline",
        botUsername: botInfo.ok ? botInfo.result.username : null,
      },
    });
  } catch (err) {
    console.error("Stats API Error:", err);
    return NextResponse.json(
      { success: false, error: err.message },
      { status: 500 }
    );
  }
}
