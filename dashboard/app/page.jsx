"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getFullCountryName } from "@/lib/countries";

export default function OverviewPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [triggering, setTriggering] = useState(false);
  const [dropResult, setDropResult] = useState(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const res = await fetch("/api/stats");
      const json = await res.json();
      if (json.success) {
        setData(json.stats);
      } else {
        setError(json.error || "Failed to load statistics");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const triggerInstantDrop = async () => {
    if (!confirm("Are you sure you want to trigger an instant giveaway drop to Telegram?")) {
      return;
    }
    try {
      setTriggering(true);
      setDropResult(null);
      const res = await fetch("/api/giveaway", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ country: "all", plan: "all" }),
      });
      const result = await res.json();
      setDropResult(result);
      if (result.success) {
        fetchStats();
      }
    } catch (err) {
      setDropResult({ success: false, error: err.message });
    } finally {
      setTriggering(false);
    }
  };

  if (loading && !data) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "60vh" }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: "2rem", marginBottom: "12px", animation: "spin 1s linear infinite" }}>⚡</div>
          <p style={{ color: "#78716c", fontWeight: 600 }}>Loading Command Center...</p>
        </div>
      </div>
    );
  }

  const {
    totalStock = 0,
    activeStock = 0,
    usedStock = 0,
    deadStock = 0,
    countryBreakdown = [],
    planBreakdown = [],
    settings = {},
    recentLogs = [],
    botStatus = "offline",
    botUsername,
  } = data || {};

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px", maxWidth: "1400px", margin: "0 auto" }}>
      {/* Welcome Banner */}
      <div
        className="glass-panel"
        style={{
          padding: "28px 32px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          background: "linear-gradient(135deg, #ffffff 0%, #fefcf8 50%, #fef8ee 100%)",
          border: "1px solid var(--border)",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <div style={{ zIndex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
            <span className="badge badge-plan-premium" style={{ fontSize: "0.75rem" }}>
              CONTROL CENTER v2.0
            </span>
            <span
              className="badge"
              style={{
                background: botStatus === "online" ? "#ecfdf5" : "#fef2f2",
                color: botStatus === "online" ? "#047857" : "#b91c1c",
                border: `1px solid ${botStatus === "online" ? "#a7f3d0" : "#fecaca"}`,
              }}
            >
              BOT: {botStatus.toUpperCase()} {botUsername ? `(@${botUsername})` : ""}
            </span>
          </div>
          <h2 style={{ fontSize: "1.75rem", fontWeight: 800, color: "#1c1917", letterSpacing: "-0.02em" }}>
            Giveaway Mission Control
          </h2>
          <p style={{ color: "#78716c", fontSize: "0.92rem", marginTop: "4px" }}>
            Manage stock, trigger Telegram drops, run live account checks, and monitor system health.
          </p>
        </div>

        <div style={{ display: "flex", gap: "12px", zIndex: 1 }}>
          <button
            onClick={triggerInstantDrop}
            disabled={triggering || activeStock === 0}
            className="btn btn-primary"
            style={{ padding: "12px 24px", fontSize: "0.95rem" }}
          >
            <span>{triggering ? "⏳" : "🚀"}</span>
            <span>{triggering ? "Dropping..." : "Instant Drop"}</span>
          </button>
          <button onClick={fetchStats} className="btn btn-secondary" style={{ padding: "12px 18px" }}>
            <span>🔄</span> Refresh
          </button>
        </div>
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
                {dropResult.success ? "✅ Giveaway Dropped!" : "❌ Drop Failed"}
              </strong>
              <p style={{ fontSize: "0.85rem", color: "#44403c", marginTop: "4px" }}>
                {dropResult.message || dropResult.error}
              </p>
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

      {/* KPI Cards Row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "20px" }}>
        {/* Active Stock */}
        <div className="glass-panel glass-panel-interactive" style={{ padding: "24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "#78716c", textTransform: "uppercase" }}>
              Active Stock
            </span>
            <span style={{ fontSize: "1.3rem" }}>📦</span>
          </div>
          <div style={{ fontSize: "2.4rem", fontWeight: 800, color: "#d97706", letterSpacing: "-0.03em" }}>
            {activeStock.toLocaleString()}
          </div>
          <div style={{ fontSize: "0.78rem", color: "#a8a29e", marginTop: "6px" }}>
            Available for instant giveaway drops
          </div>
        </div>

        {/* Drops Today */}
        <div className="glass-panel glass-panel-interactive" style={{ padding: "24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "#78716c", textTransform: "uppercase" }}>
              Drops Today
            </span>
            <span style={{ fontSize: "1.3rem" }}>🎯</span>
          </div>
          <div style={{ fontSize: "2.4rem", fontWeight: 800, color: "#b45309", letterSpacing: "-0.03em" }}>
            {settings.drops_today || 0} / {settings.drops_per_day || 3}
          </div>
          <div style={{ fontSize: "0.78rem", color: "#a8a29e", marginTop: "6px" }}>
            Interval: Every {settings.drop_interval_minutes || 120} mins
          </div>
        </div>

        {/* Total Given Away */}
        <div className="glass-panel glass-panel-interactive" style={{ padding: "24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "#78716c", textTransform: "uppercase" }}>
              Given Away
            </span>
            <span style={{ fontSize: "1.3rem" }}>🎁</span>
          </div>
          <div style={{ fontSize: "2.4rem", fontWeight: 800, color: "#16a34a", letterSpacing: "-0.03em" }}>
            {usedStock.toLocaleString()}
          </div>
          <div style={{ fontSize: "0.78rem", color: "#a8a29e", marginTop: "6px" }}>
            Total accounts distributed to users
          </div>
        </div>

        {/* Dead / Expired */}
        <div className="glass-panel glass-panel-interactive" style={{ padding: "24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "#78716c", textTransform: "uppercase" }}>
              Dead Stock
            </span>
            <span style={{ fontSize: "1.3rem" }}>🗑️</span>
          </div>
          <div style={{ fontSize: "2.4rem", fontWeight: 800, color: "#e11d48", letterSpacing: "-0.03em" }}>
            {deadStock.toLocaleString()}
          </div>
          <div style={{ fontSize: "0.78rem", color: "#a8a29e", marginTop: "6px" }}>
            <Link href="/database" style={{ color: "#e11d48", fontWeight: 600, textDecoration: "underline" }}>
              Purge Dead Accounts
            </Link>
          </div>
        </div>
      </div>

      {/* Middle Row: Country Distribution & Plans */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: "24px" }}>
        {/* Country Breakdown */}
        <div className="glass-panel" style={{ padding: "24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1c1917" }}>
              🌍 Country Distribution
            </h3>
            <span style={{ fontSize: "0.78rem", fontWeight: 600, color: "#78716c", background: "#f5efe4", padding: "4px 10px", borderRadius: "9999px" }}>
              {countryBreakdown.length} Countries
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "12px", maxHeight: "320px", overflowY: "auto", paddingRight: "4px" }}>
            {countryBreakdown.length === 0 ? (
              <p style={{ color: "#a8a29e", fontSize: "0.85rem" }}>No active stock yet.</p>
            ) : (
              countryBreakdown.map((item, idx) => {
                const pct = activeStock > 0 ? Math.round((item.count / activeStock) * 100) : 0;
                const fullCountryName = getFullCountryName(item.country);
                return (
                  <div key={idx} style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.86rem" }}>
                      <span style={{ fontWeight: 600, color: "#292524" }}>{fullCountryName}</span>
                      <span style={{ color: "#78716c", fontWeight: 500 }}>
                        <strong>{item.count.toLocaleString()}</strong> accounts ({pct}%)
                      </span>
                    </div>
                    <div style={{ height: "7px", width: "100%", background: "#f4efe6", borderRadius: "4px", overflow: "hidden" }}>
                      <div
                        style={{
                          height: "100%",
                          width: `${pct}%`,
                          background: "linear-gradient(90deg, #f59e0b, #d97706)",
                          borderRadius: "4px",
                        }}
                      />
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Plan Breakdown & Channel Info */}
        <div className="glass-panel" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "20px" }}>
          <div>
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1c1917", marginBottom: "14px" }}>
              📋 Subscription Plans
            </h3>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
              {planBreakdown.map((p, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: "10px 16px",
                    borderRadius: "12px",
                    background: "#fdfbf7",
                    border: "1px solid var(--border)",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                  }}
                >
                  <span style={{ fontWeight: 600, fontSize: "0.88rem", color: "#292524" }}>{p.plan}</span>
                  <span className="badge badge-plan-premium" style={{ fontSize: "0.75rem" }}>
                    {p.count.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ borderTop: "1px solid var(--border)", paddingTop: "16px" }}>
            <h4 style={{ fontSize: "0.95rem", fontWeight: 700, color: "#292524", marginBottom: "8px" }}>
              📢 Connected Channels
            </h4>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
              {(settings.channels || []).length === 0 ? (
                <span style={{ color: "#a8a29e", fontSize: "0.85rem" }}>
                  No channels configured. <Link href="/settings" style={{ color: "#d97706", fontWeight: 600 }}>Add in Settings</Link>
                </span>
              ) : (
                settings.channels.map((ch, idx) => (
                  <span key={idx} className="badge" style={{ background: "#fef3c7", color: "#92400e", border: "1px solid #fde68a" }}>
                    {ch}
                  </span>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity Timeline */}
      <div className="glass-panel" style={{ padding: "24px" }}>
        <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1c1917", marginBottom: "16px" }}>
          ⚡ Recent Operational Activity
        </h3>

        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {recentLogs.length === 0 ? (
            <p style={{ color: "#a8a29e", fontSize: "0.85rem" }}>No recent activity logged yet.</p>
          ) : (
            recentLogs.map((log, idx) => (
              <div
                key={idx}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "12px 16px",
                  borderRadius: "10px",
                  background: "#faf8f5",
                  border: "1px solid var(--border)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                  <span
                    style={{
                      width: "8px",
                      height: "8px",
                      borderRadius: "50%",
                      background: log.status === "success" ? "#16a34a" : "#e11d48",
                    }}
                  />
                  <div>
                    <div style={{ fontWeight: 600, fontSize: "0.88rem", color: "#1c1917" }}>
                      {log.action}
                    </div>
                    <div style={{ fontSize: "0.78rem", color: "#78716c" }}>{log.details}</div>
                  </div>
                </div>
                <div style={{ fontSize: "0.75rem", color: "#a8a29e" }}>
                  {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : ""}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
