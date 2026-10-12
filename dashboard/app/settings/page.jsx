"use client";

import { useEffect, useState } from "react";

export default function SettingsPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [intervalMins, setIntervalMins] = useState(120);
  const [dropsPerDay, setDropsPerDay] = useState(3);
  const [template, setTemplate] = useState("");
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState(null);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const res = await fetch("/api/settings");
      const json = await res.json();
      if (json.success) {
        setData(json);
        setIntervalMins(json.settings.drop_interval_minutes || 120);
        setDropsPerDay(json.settings.drops_per_day || 3);
        setTemplate(json.settings.custom_template || "");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          drop_interval_minutes: intervalMins,
          drops_per_day: dropsPerDay,
          custom_template: template,
        }),
      });
      const json = await res.json();
      if (json.success) {
        setMsg({ type: "success", text: "Settings saved successfully!" });
        fetchSettings();
      }
    } catch (err) {
      setMsg({ type: "error", text: err.message });
    } finally {
      setSaving(false);
    }
  };

  const bot = data?.bot;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px", maxWidth: "1400px", margin: "0 auto" }}>
      <div>
        <h2 style={{ fontSize: "1.75rem", fontWeight: 800, color: "#1c1917", letterSpacing: "-0.02em" }}>
          Bot Configuration & System Settings
        </h2>
        <p style={{ color: "#78716c", fontSize: "0.9rem" }}>
          Configure operational parameters, Telegram Bot API credentials, and Vercel environment.
        </p>
      </div>

      {msg && (
        <div
          className="glass-panel"
          style={{
            padding: "16px 20px",
            borderLeft: `4px solid ${msg.type === "success" ? "#16a34a" : "#e11d48"}`,
            background: msg.type === "success" ? "#f0fdf4" : "#fef2f2",
          }}
        >
          <span style={{ color: msg.type === "success" ? "#15803d" : "#991b1b", fontWeight: 600 }}>{msg.text}</span>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))", gap: "24px" }}>
        {/* Bot Information Card */}
        <div className="glass-panel" style={{ padding: "28px", display: "flex", flexDirection: "column", gap: "16px" }}>
          <h3 style={{ fontSize: "1.15rem", fontWeight: 700, color: "#1c1917" }}>
            🤖 Telegram Bot Status
          </h3>

          <div
            style={{
              padding: "16px",
              borderRadius: "12px",
              background: "#faf8f5",
              border: "1px solid var(--border)",
              display: "flex",
              flexDirection: "column",
              gap: "10px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.88rem" }}>
              <span style={{ color: "#78716c", fontWeight: 600 }}>Connection:</span>
              <span className={`badge ${bot?.ok ? "badge-active" : "badge-dead"}`}>
                {bot?.ok ? "CONNECTED 🟢" : "OFFLINE / UNCONFIGURED"}
              </span>
            </div>
            {bot?.ok && (
              <>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.88rem" }}>
                  <span style={{ color: "#78716c", fontWeight: 600 }}>Bot Username:</span>
                  <span style={{ fontWeight: 700, color: "#d97706" }}>@{bot.result?.username}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.88rem" }}>
                  <span style={{ color: "#78716c", fontWeight: 600 }}>Bot Name:</span>
                  <span style={{ fontWeight: 600, color: "#1c1917" }}>{bot.result?.first_name}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.88rem" }}>
                  <span style={{ color: "#78716c", fontWeight: 600 }}>Bot ID:</span>
                  <span style={{ color: "#44403c" }}>{bot.result?.id}</span>
                </div>
              </>
            )}
          </div>

          {/* Vercel Deployment Checklist */}
          <div style={{ marginTop: "10px" }}>
            <h4 style={{ fontSize: "0.95rem", fontWeight: 700, color: "#1c1917", marginBottom: "10px" }}>
              🌐 Vercel Deployment Checklist
            </h4>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "0.84rem", color: "#44403c" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span>✅</span> <code>MONGO_URI</code> configured for database connection
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span>✅</span> <code>BOT_TOKEN</code> configured for Telegram broadcast
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span>✅</span> <code>OWNER_ID</code> configured for admin privileges
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span>✅</span> <code>CHANNEL_IDS</code> configured for broadcast
              </div>
            </div>
          </div>
        </div>

        {/* Global Bot Settings Form */}
        <div className="glass-panel" style={{ padding: "28px" }}>
          <h3 style={{ fontSize: "1.15rem", fontWeight: 700, color: "#1c1917", marginBottom: "18px" }}>
            ⚙️ Operational Settings
          </h3>

          <form onSubmit={handleSave} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div>
              <label style={{ fontSize: "0.82rem", color: "#78716c", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                Drop Interval (Minutes between auto drops)
              </label>
              <input
                type="number"
                min="10"
                max="1440"
                className="input-control"
                value={intervalMins}
                onChange={(e) => setIntervalMins(Number(e.target.value))}
              />
            </div>

            <div>
              <label style={{ fontSize: "0.82rem", color: "#78716c", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                Drops Allowed Per Day
              </label>
              <input
                type="number"
                min="1"
                max="100"
                className="input-control"
                value={dropsPerDay}
                onChange={(e) => setDropsPerDay(Number(e.target.value))}
              />
            </div>

            <div>
              <label style={{ fontSize: "0.82rem", color: "#78716c", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                Custom Broadcast Template (Markdown)
              </label>
              <textarea
                rows={5}
                className="input-control"
                placeholder="🎉 NETFLIX DROP 🎉\n\nCountry: {country}\nPlan: {plan}..."
                value={template}
                onChange={(e) => setTemplate(e.target.value)}
              />
            </div>

            <button type="submit" disabled={saving} className="btn btn-primary" style={{ padding: "12px", marginTop: "8px" }}>
              {saving ? "Saving Changes..." : "💾 Save Operational Settings"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
