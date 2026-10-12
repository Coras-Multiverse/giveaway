import { NextResponse } from "next/server";
import { getDatabase } from "@/lib/mongodb";
import { getBotMe } from "@/lib/telegram";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const db = await getDatabase();
    const settingsCol = db.collection("settings");
    const settings = (await settingsCol.findOne({ _id: "config" })) || {
      channels: [],
      drop_interval_minutes: 120,
      drops_per_day: 3,
      drops_today: 0,
      last_drop_time: null,
      custom_template: "",
    };

    const botInfo = await getBotMe();

    return NextResponse.json({
      success: true,
      settings,
      bot: botInfo,
    });
  } catch (err) {
    console.error("Settings GET Error:", err);
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}

export async function POST(request) {
  try {
    const body = await request.json();
    const db = await getDatabase();
    const settingsCol = db.collection("settings");
    const logsCol = db.collection("activity_logs");

    const updateFields = {};
    if (body.channels !== undefined) updateFields.channels = body.channels;
    if (body.drop_interval_minutes !== undefined)
      updateFields.drop_interval_minutes = parseInt(body.drop_interval_minutes, 10);
    if (body.drops_per_day !== undefined)
      updateFields.drops_per_day = parseInt(body.drops_per_day, 10);
    if (body.drops_today !== undefined)
      updateFields.drops_today = parseInt(body.drops_today, 10);
    if (body.custom_template !== undefined)
      updateFields.custom_template = body.custom_template;

    await settingsCol.updateOne(
      { _id: "config" },
      { $set: updateFields },
      { upsert: true }
    );

    await logsCol.insertOne({
      action: "SETTINGS_UPDATED",
      details: `Updated settings fields: ${Object.keys(updateFields).join(", ")}`,
      status: "success",
      timestamp: new Date(),
    });

    return NextResponse.json({ success: true, message: "Settings updated successfully" });
  } catch (err) {
    console.error("Settings POST Error:", err);
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}
