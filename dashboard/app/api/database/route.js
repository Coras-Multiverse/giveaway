import { NextResponse } from "next/server";
import { getDatabase } from "@/lib/mongodb";

export const dynamic = "force-dynamic";

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const action = searchParams.get("action");
    const db = await getDatabase();
    const stockCol = db.collection("stock");

    if (action === "export_backup") {
      const allStock = await stockCol.find({}).toArray();
      return new Response(JSON.stringify(allStock, null, 2), {
        status: 200,
        headers: {
          "Content-Type": "application/json",
          "Content-Disposition": 'attachment; filename="stock_backup.json"',
        },
      });
    }

    // Default: Return database statistics
    const stats = await stockCol.stats().catch(() => ({}));
    const totalCount = await stockCol.countDocuments({});
    const activeCount = await stockCol.countDocuments({ status: "active" });
    const deadCount = await stockCol.countDocuments({ status: "dead" });
    const givenCount = await stockCol.countDocuments({ status: "given" });

    return NextResponse.json({
      success: true,
      stats: {
        totalCount,
        activeCount,
        deadCount,
        givenCount,
        storageSize: stats.storageSize || 0,
        avgObjSize: stats.avgObjSize || 0,
      },
    });
  } catch (err) {
    console.error("Database API Error:", err);
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}

export async function POST(request) {
  try {
    const body = await request.json();
    const { action } = body;
    const db = await getDatabase();
    const stockCol = db.collection("stock");
    const logsCol = db.collection("activity_logs");

    if (action === "purge_dead") {
      const result = await stockCol.deleteMany({ status: "dead" });
      await logsCol.insertOne({
        action: "PURGE_DEAD_STOCK",
        details: `Deleted ${result.deletedCount} dead stock accounts`,
        status: "success",
        timestamp: new Date(),
      });
      return NextResponse.json({
        success: true,
        message: `Purged ${result.deletedCount} dead account(s).`,
      });
    }

    if (action === "clean_given") {
      const result = await stockCol.deleteMany({ status: "given" });
      await logsCol.insertOne({
        action: "CLEAN_GIVEN_STOCK",
        details: `Deleted ${result.deletedCount} given stock accounts`,
        status: "success",
        timestamp: new Date(),
      });
      return NextResponse.json({
        success: true,
        message: `Cleaned ${result.deletedCount} previously given account(s).`,
      });
    }

    return NextResponse.json({ success: false, error: "Invalid action" }, { status: 400 });
  } catch (err) {
    console.error("Database POST Error:", err);
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}
