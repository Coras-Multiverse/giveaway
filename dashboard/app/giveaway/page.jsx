"use client";

import { useEffect, useState } from "react";
import { COUNTRY_MAP, getFullCountryName } from "@/lib/countries";

export default function GiveawayPage() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);

  // Drop Form
  const [selectedCountry, setSelectedCountry] = useState("all");
  const [selectedPlan, setSelectedPlan] = useState("all");
  const [targetChannel, setTargetChannel] = useState("");
  const [customMsg, setCustomMsg] = useState("");
  const [dropping, setDropping] = useState(false);
  const [dropResult, setDropResult] = useState(null);

  // Scheduler Form
  const [intervalMins, setIntervalMins] = useState(120);
  const [maxDrops, setMaxDrops] = useState(3);
  const [savingSettings, setSavingSettings] = useState(false);

  // Channel Manager Form
  const [newChannel, setNewChannel] = useState("");

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const res = await fetch("/api/settings");
      const json = await res.json();
      if (json.success) {
        setSettings(json.settings);
        setIntervalMins(json.settings.drop_interval_minutes || 120);
        setMaxDrops(json.settings.drops_per_day || 3);
        setCustomMsg(json.settings.custom_template || "");
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

  const handleTriggerDrop = async () => {
    try {
      setDropping(true);
      setDropResult(null);

      const res = await fetch("/api/giveaway", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          country: selectedCountry,
          plan: selectedPlan,
          channel: targetChannel || undefined,
          customMessage: customMsg || undefined,
        }),
      });

      const json = await res.json();
      setDropResult(json);
      if (json.success) {
        fetchSettings();
      }
    } catch (err) {
      setDropResult({ success: false, error: err.message });
    } finally {
      setDropping(false);
    }
  };

  const saveSchedulerSettings = async () => {
    try {
      setSavingSettings(true);
      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          drop_interval_minutes: intervalMins,
          drops_per_day: maxDrops,
          custom_template: customMsg,
        }),
      });
      const json = await res.json();
      if (json.success) {
        alert("Scheduler configuration saved successfully!");
        fetchSettings();
      }
    } catch (err) {
      alert("Failed to save: " + err.message);
    } finally {
      setSavingSettings(false);
    }
  };

  const addChannel = async () => {
    if (!newChannel.trim()) return;
    const currentChannels = settings?.channels || [];
    if (currentChannels.includes(newChannel.trim())) {
      alert("Channel already added!");
      return;
    }
    const updated = [...currentChannels, newChannel.trim()];
    try {
      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channels: updated }),
      });
      const json = await res.json();
      if (json.success) {
        setNewChannel("");
        fetchSettings();
      }
    } catch (err) {
      alert("Failed to add channel: " + err.message);
    }
  };

  const removeChannel = async (ch) => {
    const currentChannels = settings?.channels || [];
    const updated = currentChannels.filter((c) => c !== ch);
    try {
      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channels: updated }),
      });
      const json = await res.json();
      if (json.success) {
        fetchSettings();
      }
    } catch (err) {
      alert("Failed to remove channel: " + err.message);
    }
  };

  const resetTodayCounter = async () => {
    if (!confirm("Reset daily drops counter to 0?")) return;
    try {
      await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ drops_today: 0 }),
      });
      fetchSettings();
    } catch (err) {
      alert(err.message);
    }
  };

  // Sorted list of unique country names for dropdown
  const countryOptions = Array.from(new Set(Object.values(COUNTRY_MAP))).sort((a, b) => a.localeCompare(b));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px", maxWidth: "1400px", margin: "0 auto" }}>
      <div>
        <h2 style={{ fontSize: "1.75rem", fontWeight: 800, color: "#1c1917", letterSpacing: "-0.02em" }}>
          Giveaway Automation & Instant Drops
        </h2>
        <p style={{ color: "#78716c", fontSize: "0.9rem" }}>
          Configure broadcast channels, custom template formats, and trigger manual or scheduled drops.
        </p>
      </div>

      {dropResult && (
        <div
          className="glass-panel"
          style={{
            padding: "16px 20px",
            borderLeft: `4px solid ${dropResult.success ? "#16a34a" : "#e11d48"}`,
            background: dropResult.success ? "#f0fdf4" : "#fef2f2",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <strong style={{ color: dropResult.success ? "#15803d" : "#991b1b" }}>
                {dropResult.success ? "🎉 Drop Successful!" : "❌ Drop Failed"}
              </strong>
              <p style={{ fontSize: "0.85rem", color: "#44403c", marginTop: "4px" }}>
                {dropResult.message || dropResult.error}
              </p>
              {dropResult.droppedItem && (
                <div style={{ fontSize: "0.8rem", color: "#78716c", marginTop: "4px" }}>
                  Account: <strong>{dropResult.droppedItem.email}</strong> | Plan: {dropResult.droppedItem.plan} | Country: {getFullCountryName(dropResult.droppedItem.country)}
                </div>
              )}
            </div>
            <button
              onClick={() => setDropResult(null)}
              style={{ background: "none", border: "none", color: "#78716c", cursor: "pointer", fontSize: "1.2rem" }}
            >
              ×
            </button>
          </div>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))", gap: "24px" }}>
        {/* Instant Drop Launcher Card */}
        <div className="glass-panel" style={{ padding: "28px", display: "flex", flexDirection: "column", gap: "20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "1.5rem" }}>🚀</span>
            <div>
              <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "#1c1917" }}>
                Trigger Instant Drop
              </h3>
              <p style={{ fontSize: "0.82rem", color: "#78716c" }}>
                Picks active stock and broadcasts immediately to Telegram
              </p>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div>
                <label style={{ fontSize: "0.8rem", color: "#78716c", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                  Country (Full Name)
                </label>
                <select
                  className="input-control"
                  value={selectedCountry}
                  onChange={(e) => setSelectedCountry(e.target.value)}
                >
                  <option value="all">Any Country (Global)</option>
                  {countryOptions.map((c, idx) => (
                    <option key={idx} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ fontSize: "0.8rem", color: "#78716c", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                  Plan Filter
                </label>
                <select
                  className="input-control"
                  value={selectedPlan}
                  onChange={(e) => setSelectedPlan(e.target.value)}
                >
                  <option value="all">Any Plan</option>
                  <option value="Premium">Premium 4K</option>
                  <option value="Standard">Standard HD</option>
                  <option value="Basic">Basic</option>
                </select>
              </div>
            </div>

            <div>
              <label style={{ fontSize: "0.8rem", color: "#78716c", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                Target Channel (Leave blank to broadcast to all configured)
              </label>
              <select
                className="input-control"
                value={targetChannel}
                onChange={(e) => setTargetChannel(e.target.value)}
              >
                <option value="">All Configured Channels</option>
                {(settings?.channels || []).map((ch, idx) => (
                  <option key={idx} value={ch}>
                    {ch}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ fontSize: "0.8rem", color: "#78716c", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                Custom Broadcast Message Template (Leave blank for official bot drop format)
              </label>
              <textarea
                rows={3}
                className="input-control"
                placeholder="Leave blank to use the official bot drop format shown below..."
                value={customMsg}
                onChange={(e) => setCustomMsg(e.target.value)}
              />
            </div>

            {/* Telegram Official Drop Preview */}
            <div
              style={{
                borderRadius: "12px",
                background: "#fdfbf7",
                border: "1px solid #fed7aa",
                padding: "16px",
                display: "flex",
                flexDirection: "column",
                gap: "10px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.8rem", fontWeight: 700, color: "#b45309" }}>
                <span>📬</span> Official Telegram Drop Preview (Matches Bot 100%)
              </div>

              {/* Document File Preview */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  padding: "10px 14px",
                  borderRadius: "8px",
                  background: "#ffffff",
                  border: "1px solid #e7e5e4",
                }}
              >
                <div
                  style={{
                    width: "36px",
                    height: "36px",
                    borderRadius: "50%",
                    background: "#0284c7",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#ffffff",
                    fontSize: "1.1rem",
                  }}
                >
                  ↓
                </div>
                <div>
                  <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#1c1917" }}>
                    example_account@domain.com_account.txt
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#78716c" }}>2.5 KB · Text Document</div>
                </div>
              </div>

              {/* Caption Preview */}
              <div
                style={{
                  fontSize: "0.84rem",
                  color: "#1c1917",
                  lineHeight: 1.6,
                  whiteSpace: "pre-line",
                  fontFamily: "inherit",
                }}
              >
                {customMsg
                  ? customMsg
                      .replace("{country}", selectedCountry === "all" ? "Japan 🇯🇵" : selectedCountry)
                      .replace("{plan}", selectedPlan === "all" ? "Premium" : selectedPlan)
                      .replace("{email}", "example_account@domain.com")
                  : `🎁 *New Drop!*\n\n🌍 *Country:* ${selectedCountry === "all" ? "Japan 🇯🇵" : selectedCountry}\n📺 *Plan:* ${selectedPlan === "all" ? "Premium" : selectedPlan}\n\n🔗 *Direct Login Link:* Click Here to Login\n\n🌟 *Provided By:* @iq4u8 & @xxbga\n📢 *Join us:* Giveaway Hub`}
              </div>
            </div>

            <button
              onClick={handleTriggerDrop}
              disabled={dropping}
              className="btn btn-primary"
              style={{ padding: "14px", fontSize: "1rem", marginTop: "8px" }}
            >
              <span>{dropping ? "⏳" : "⚡"}</span>
              <span>{dropping ? "Broadcasting to Telegram..." : "Launch Drop Now"}</span>
            </button>
          </div>
        </div>

        {/* Auto-Drop Schedule Settings */}
        <div className="glass-panel" style={{ padding: "28px", display: "flex", flexDirection: "column", gap: "20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "1.5rem" }}>⏱️</span>
            <div>
              <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "#1c1917" }}>
                Scheduler & Automation
              </h3>
              <p style={{ fontSize: "0.82rem", color: "#78716c" }}>
                Controls automated background giveaway loops
              </p>
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                <label style={{ fontSize: "0.85rem", fontWeight: 600, color: "#292524" }}>Drop Interval (Minutes)</label>
                <span style={{ color: "#d97706", fontWeight: 700 }}>{intervalMins} mins</span>
              </div>
              <input
                type="range"
                min="10"
                max="720"
                step="10"
                value={intervalMins}
                onChange={(e) => setIntervalMins(Number(e.target.value))}
                style={{ width: "100%", accentColor: "#d97706" }}
              />
            </div>

            <div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                <label style={{ fontSize: "0.85rem", fontWeight: 600, color: "#292524" }}>Max Drops Per Day</label>
                <span style={{ color: "#d97706", fontWeight: 700 }}>{maxDrops} drops</span>
              </div>
              <input
                type="range"
                min="1"
                max="50"
                value={maxDrops}
                onChange={(e) => setMaxDrops(Number(e.target.value))}
                style={{ width: "100%", accentColor: "#d97706" }}
              />
            </div>

            <div
              style={{
                padding: "14px",
                borderRadius: "10px",
                background: "#faf8f5",
                border: "1px solid var(--border)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div>
                <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "#1c1917" }}>Daily Drop Progress</div>
                <div style={{ fontSize: "0.78rem", color: "#78716c" }}>
                  {settings?.drops_today || 0} of {maxDrops} completed today
                </div>
              </div>
              <button onClick={resetTodayCounter} className="btn btn-secondary" style={{ padding: "6px 12px", fontSize: "0.78rem" }}>
                Reset Counter
              </button>
            </div>

            <button
              onClick={saveSchedulerSettings}
              disabled={savingSettings}
              className="btn btn-yellow"
              style={{ padding: "12px", fontWeight: 700 }}
            >
              {savingSettings ? "Saving Settings..." : "💾 Save Schedule Settings"}
            </button>
          </div>
        </div>
      </div>

      {/* Connected Channels Manager Card */}
      <div className="glass-panel" style={{ padding: "28px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
          <div>
            <h3 style={{ fontSize: "1.2rem", fontWeight: 700, color: "#1c1917" }}>
              📢 Connected Broadcast Channels
            </h3>
            <p style={{ fontSize: "0.82rem", color: "#78716c" }}>
              Channels where giveaway accounts and cookies will be posted
            </p>
          </div>
        </div>

        {/* Add Channel Input */}
        <div style={{ display: "flex", gap: "10px", marginBottom: "20px" }}>
          <input
            type="text"
            className="input-control"
            placeholder="Enter channel handle (e.g. @MyGiveawayChannel) or ID (-100...)"
            value={newChannel}
            onChange={(e) => setNewChannel(e.target.value)}
            style={{ maxWidth: "450px" }}
          />
          <button onClick={addChannel} className="btn btn-primary">
            ➕ Add Channel
          </button>
        </div>

        {/* Channels List */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: "12px" }}>
          {(settings?.channels || []).length === 0 ? (
            <p style={{ color: "#a8a29e", fontSize: "0.85rem" }}>
              No channels added yet. Add your Telegram channel above to start broadcasting drops!
            </p>
          ) : (
            settings.channels.map((ch, idx) => (
              <div
                key={idx}
                style={{
                  padding: "14px 18px",
                  borderRadius: "12px",
                  background: "#fbf9f5",
                  border: "1px solid var(--border)",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "1.1rem" }}>📡</span>
                  <span style={{ fontWeight: 600, fontSize: "0.9rem", color: "#1c1917" }}>{ch}</span>
                </div>
                <button
                  onClick={() => removeChannel(ch)}
                  className="btn btn-danger"
                  style={{ padding: "4px 8px", fontSize: "0.75rem" }}
                  title="Remove"
                >
                  ✕
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
