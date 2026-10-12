const BOT_TOKEN = process.env.BOT_TOKEN;

/**
 * Send a text message to a Telegram chat/channel using Telegram Bot API.
 */
export async function sendTelegramMessage(chatId, text, parseMode = "Markdown") {
  if (!BOT_TOKEN) {
    throw new Error("BOT_TOKEN is not configured in environment variables.");
  }

  const url = `https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text: text,
      parse_mode: parseMode,
      disable_web_page_preview: false,
    }),
  });

  const data = await response.json();
  if (!data.ok) {
    throw new Error(data.description || "Failed to send Telegram message");
  }
  return data.result;
}

/**
 * Send document (e.g. cookie TXT or JSON file) to a Telegram chat/channel.
 */
export async function sendTelegramDocument(chatId, fileBuffer, fileName, caption = "", parseMode = "Markdown") {
  if (!BOT_TOKEN) {
    throw new Error("BOT_TOKEN is not configured in environment variables.");
  }

  const url = `https://api.telegram.org/bot${BOT_TOKEN}/sendDocument`;
  const formData = new FormData();
  formData.append("chat_id", chatId);
  const blob = typeof fileBuffer === "string" ? new Blob([fileBuffer], { type: "text/plain" }) : new Blob([fileBuffer]);
  formData.append("document", blob, fileName);
  if (caption) {
    formData.append("caption", caption);
    formData.append("parse_mode", parseMode);
  }

  const response = await fetch(url, {
    method: "POST",
    body: formData,
  });

  const data = await response.json();
  if (!data.ok) {
    throw new Error(data.description || "Failed to send document to Telegram");
  }
  return data.result;
}

/**
 * Check if the bot token is valid and retrieve bot information.
 */
export async function getBotMe() {
  if (!BOT_TOKEN) {
    return { ok: false, error: "BOT_TOKEN not provided" };
  }
  try {
    const url = `https://api.telegram.org/bot${BOT_TOKEN}/getMe`;
    const response = await fetch(url, { method: "GET" });
    const data = await response.json();
    return data;
  } catch (err) {
    return { ok: false, error: err.message };
  }
}
