import { NextResponse } from "next/server";
import { getDatabase } from "@/lib/mongodb";
import { ObjectId } from "mongodb";
import { getFullCountryName } from "@/lib/countries";

export const dynamic = "force-dynamic";

import { standardizePlan } from "@/lib/plans";

export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get("page") || "1", 10);
    const limit = parseInt(searchParams.get("limit") || "30", 10);
    const country = searchParams.get("country");
    const plan = searchParams.get("plan");
    const status = searchParams.get("status") || "active";
    const search = searchParams.get("search");

    const query = {};
    if (status && status !== "all") {
      query.status = status;
    }
    if (country && country !== "all") {
      query.country = country;
    }
    if (plan && plan !== "all") {
      query.$or = [{ standard_plan: plan }, { plan: { $regex: plan, $options: "i" } }];
    }
    if (search) {
      query.$or = [
        { email: { $regex: search, $options: "i" } },
        { country: { $regex: search, $options: "i" } },
        { plan: { $regex: search, $options: "i" } },
      ];
    }

    const db = await getDatabase();
    const stockCol = db.collection("stock");

    const total = await stockCol.countDocuments(query);
    const skip = (page - 1) * limit;

    const items = await stockCol
      .find(query)
      .sort({ _id: -1 })
      .skip(skip)
      .limit(limit)
      .toArray();

    return NextResponse.json({
      success: true,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
      items: items.map((item) => ({
        ...item,
        _id: item._id.toString(),
        country: getFullCountryName(item.country),
        plan: standardizePlan(item.plan, item.standard_plan),
      })),
    });
  } catch (err) {
    console.error("Stock GET Error:", err);
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}

export async function POST(request) {
  try {
    const body = await request.json();
    const db = await getDatabase();
    const stockCol = db.collection("stock");
    const logsCol = db.collection("activity_logs");

    // Single item or array of items
    const rawItems = Array.isArray(body) ? body : [body];
    let insertedCount = 0;

    for (const item of rawItems) {
      if (!item.email || !item.cookies) continue;

      const stdPlan = item.standard_plan || standardizePlan(item.plan || "");
      await stockCol.updateOne(
        { email: item.email },
        {
          $set: {
            country: item.country || "Unknown",
            email: item.email,
            plan: item.plan || "Premium",
            standard_plan: stdPlan,
            payment: item.payment || "N/A",
            cookies: item.cookies,
            password: item.password || null,
            status: item.status || "active",
            updatedAt: new Date(),
          },
        },
        { upsert: true }
      );
      insertedCount++;
    }

    await logsCol.insertOne({
      action: "STOCK_ADDED",
      details: `Added/Updated ${insertedCount} stock account(s)`,
      status: "success",
      timestamp: new Date(),
    });

    return NextResponse.json({
      success: true,
      message: `Successfully processed ${insertedCount} account(s)`,
      count: insertedCount,
    });
  } catch (err) {
    console.error("Stock POST Error:", err);
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}

export async function DELETE(request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get("id");
    const email = searchParams.get("email");

    const db = await getDatabase();
    const stockCol = db.collection("stock");
    const logsCol = db.collection("activity_logs");

    if (id) {
      await stockCol.deleteOne({ _id: new ObjectId(id) });
    } else if (email) {
      await stockCol.deleteOne({ email });
    } else {
      // Bulk delete via request body
      const body = await request.json();
      if (body.emails && Array.isArray(body.emails)) {
        await stockCol.deleteMany({ email: { $in: body.emails } });
      }
    }

    await logsCol.insertOne({
      action: "STOCK_DELETED",
      details: `Deleted stock item: ${email || id || "bulk"}`,
      status: "success",
      timestamp: new Date(),
    });

    return NextResponse.json({ success: true, message: "Stock deleted successfully" });
  } catch (err) {
    console.error("Stock DELETE Error:", err);
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}

export async function PUT(request) {
  try {
    const body = await request.json();
    const { id, email, status, country, plan } = body;

    const db = await getDatabase();
    const stockCol = db.collection("stock");

    const updateQuery = {};
    if (status) updateQuery.status = status;
    if (country) updateQuery.country = country;
    if (plan) {
      updateQuery.plan = plan;
      updateQuery.standard_plan = standardizePlan(plan);
    }

    if (id) {
      await stockCol.updateOne({ _id: new ObjectId(id) }, { $set: updateQuery });
    } else if (email) {
      await stockCol.updateOne({ email }, { $set: updateQuery });
    }

    return NextResponse.json({ success: true, message: "Stock updated successfully" });
  } catch (err) {
    console.error("Stock PUT Error:", err);
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}
