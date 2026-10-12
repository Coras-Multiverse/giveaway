"use client";

import { useState } from "react";

export default function CheckerStudioPage() {
  const [service, setService] = useState("netflix_cookie");
  const [inputContent, setInputContent] = useState("");
  const [checking, setChecking] = useState(false);
  const [logs, setLogs] = useState([]);
  const [lastHit, setLastHit] = useState(null);
  const [saving, setSaving] = useState(false);

  const addLog = (type, message) => {
    setLogs((prev) => [
      {
        id: Date.now() + Math.random(),
        time: new Date().toLocaleTimeString(),
        type,
        message,
      },
      ...prev,
    ]);
  };

  const handleCheck = async () => {
    if (!inputContent.trim()) return;
    try {
      setChecking(true);
      addLog("INFO", `Checking ${service.toUpperCase()} input...`);

      const res = await fetch("/api/checker", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: service, content: inputContent.trim() }),
      });

      const json = await res.json();
      if (json.status === "HIT") {
        addLog("HIT", `🎉 [HIT] ${json.message}`);
        setLastHit({
          service,
          raw: inputContent.trim(),
          data: json.data,
        });
      } else if (json.status === "BAD") {
        addLog("BAD", `❌ [BAD] ${json.message}`);
      } else {
        addLog("WARN", `⚠️ [${json.status || "RESP"}] ${json.message}`);
      }
    } catch (err) {
      addLog("ERROR", `🔥 [ERROR] ${err.message}`);
    } finally {
      setChecking(false);
    }
  };

  const saveHitToStock = async () => {
    if (!lastHit) return;
    try {
      setSaving(true);
      const email = lastHit.data?.email || `verified_${Date.now()}@hit.com`;
      const res = await fetch("/api/stock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          country: "Verified Country",
          plan: "Premium",
          payment: "Verified",
          cookies: lastHit.raw,
          status: "active",
        }),
      });
      const json = await res.json();
      if (json.success) {
        addLog("SUCCESS", `✅ Account ${email} saved directly into active giveaway stock!`);
        setLastHit(null);
      }
    } catch (err) {
      addLog("ERROR", `Failed to save: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px", maxWidth: "1400px", margin: "0 auto" }}>
      <div>
        <h2 style={{ fontSize: "1.75rem", fontWeight: 800, color: "#1c1917", letterSpacing: "-0.02em" }}>
          Live Checker Studio
        </h2>
        <p style={{ color: "#78716c", fontSize: "0.9rem" }}>
          Validate Netflix cookies, NFToken links, and Crunchyroll combos live from your browser.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(450px, 1fr))", gap: "24px" }}>
        {/* Input Card */}
        <div className="glass-panel" style={{ padding: "28px", display: "flex", flexDirection: "column", gap: "18px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ fontSize: "1.15rem", fontWeight: 700, color: "#1c1917" }}>
              Input & Service Configuration
            </h3>
            <span className="badge badge-plan-premium">Active Engine</span>
          </div>

          <div>
            <label style={{ fontSize: "0.82rem", color: "#78716c", fontWeight: 600, display: "block", marginBottom: "6px" }}>
              Select Verification Service
            </label>
            <div style={{ display: "flex", gap: "10px" }}>
              <button
                type="button"
                onClick={() => setService("netflix_cookie")}
                className={`btn ${service === "netflix_cookie" ? "btn-primary" : "btn-secondary"}`}
                style={{ flex: 1 }}
              >
                🔴 Netflix Cookies / Token
              </button>
              <button
                type="button"
                onClick={() => setService("crunchyroll")}
                className={`btn ${service === "crunchyroll" ? "btn-primary" : "btn-secondary"}`}
                style={{ flex: 1 }}
              >
                🟠 Crunchyroll Auth
              </button>
            </div>
          </div>

          <div>
            <label style={{ fontSize: "0.82rem", color: "#78716c", fontWeight: 600, display: "block", marginBottom: "6px" }}>
              {service === "netflix_cookie"
                ? "Paste Netscape cookies, JSON cookie array, or NetflixId string:"
                : "Paste Crunchyroll Email:Password combo:"}
            </label>
            <textarea
              rows={8}
              className="input-control"
              placeholder={
                service === "netflix_cookie"
                  ? ".netflix.com	TRUE	/	TRUE	1798765432	NetflixId	v%3D3..."
                  : "user@example.com:password123"
              }
              value={inputContent}
              onChange={(e) => setInputContent(e.target.value)}
            />
          </div>

          <div style={{ display: "flex", gap: "10px" }}>
            <button
              onClick={handleCheck}
              disabled={checking || !inputContent.trim()}
              className="btn btn-primary"
              style={{ flex: 1, padding: "12px", fontSize: "0.95rem" }}
            >
              <span>{checking ? "⏳" : "⚡"}</span>
              <span>{checking ? "Checking Account..." : "Run Live Verification"}</span>
            </button>
            <button
              onClick={() => {
                setInputContent("");
                setLastHit(null);
              }}
              className="btn btn-secondary"
            >
              Clear
            </button>
          </div>

          {lastHit && (
            <div
              style={{
                padding: "16px",
                borderRadius: "12px",
                background: "#f0fdf4",
                border: "1px solid #bbf7d0",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <div>
                <span className="badge badge-active" style={{ marginBottom: "4px" }}>
                  WORKING HIT FOUND
                </span>
                <div style={{ fontSize: "0.85rem", color: "#166534", fontWeight: 600 }}>
                  Ready to be added to active giveaway stock.
                </div>
              </div>
              <button onClick={saveHitToStock} disabled={saving} className="btn btn-success">
                {saving ? "Saving..." : "💾 Add to Stock"}
              </button>
            </div>
          )}
        </div>

        {/* Live Terminal Output Card */}
        <div
          className="glass-panel"
          style={{
            padding: "24px",
            display: "flex",
            flexDirection: "column",
            background: "#fcfbf7",
            border: "1px solid var(--border)",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              paddingBottom: "12px",
              borderBottom: "1px solid var(--border)",
              marginBottom: "14px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#f87171" }} />
              <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#fbbf24" }} />
              <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#34d399" }} />
              <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "#78716c", marginLeft: "6px" }}>
                TERMINAL OUTPUT LOG
              </span>
            </div>
            <button
              onClick={() => setLogs([])}
              style={{ background: "none", border: "none", color: "#a8a29e", cursor: "pointer", fontSize: "0.75rem", fontWeight: 600 }}
            >
              Clear Logs
            </button>
          </div>

          <div
            style={{
              flex: 1,
              minHeight: "320px",
              maxHeight: "450px",
              overflowY: "auto",
              fontFamily: "monospace",
              fontSize: "0.82rem",
              display: "flex",
              flexDirection: "column",
              gap: "8px",
              background: "#ffffff",
              padding: "16px",
              borderRadius: "10px",
              border: "1px solid #f0eae1",
            }}
          >
            {logs.length === 0 ? (
              <div style={{ color: "#a8a29e", padding: "40px 0", textAlign: "center" }}>
                Ready. Run an account verification to view live output here.
              </div>
            ) : (
              logs.map((log) => {
                let color = "#292524";
                if (log.type === "HIT" || log.type === "SUCCESS") color = "#15803d";
                if (log.type === "BAD") color = "#b91c1c";
                if (log.type === "ERROR") color = "#b91c1c";
                if (log.type === "WARN") color = "#b45309";
                return (
                  <div key={log.id} style={{ display: "flex", gap: "10px", lineHeight: "1.4" }}>
                    <span style={{ color: "#a8a29e" }}>[{log.time}]</span>
                    <span style={{ color, fontWeight: log.type === "HIT" ? 700 : 500 }}>{log.message}</span>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
