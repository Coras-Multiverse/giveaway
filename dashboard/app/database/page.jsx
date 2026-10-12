"use client";

import { useEffect, useState } from "react";

export default function DatabasePage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [purging, setPurging] = useState(false);
  const [message, setMessage] = useState(null);

  const fetchDbStats = async () => {
    try {
      setLoading(true);
      const res = await fetch("/api/database");
      const json = await res.json();
      if (json.success) {
        setStats(json.stats);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDbStats();
  }, []);

  const handleAction = async (action, confirmMsg) => {
    if (!confirm(confirmMsg)) return;
    try {
      setPurging(true);
      setMessage(null);
      const res = await fetch("/api/database", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
      const json = await res.json();
      setMessage(json.message);
      fetchDbStats();
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      setPurging(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px", maxWidth: "1400px", margin: "0 auto" }}>
      <div>
        <h2 style={{ fontSize: "1.75rem", fontWeight: 800, color: "#1c1917", letterSpacing: "-0.02em" }}>
          Database Maintenance & Purge Center
        </h2>
        <p style={{ color: "#78716c", fontSize: "0.9rem" }}>
          Clean expired accounts, optimize MongoDB collections, and export full database backups.
        </p>
      </div>

      {message && (
        <div
          className="glass-panel"
          style={{
            padding: "16px 20px",
            borderLeft: "4px solid #16a34a",
            background: "#f0fdf4",
            display: "flex",
            justifyContent: "space-between",
          }}
        >
          <span style={{ color: "#15803d", fontWeight: 600 }}>{message}</span>
          <button onClick={() => setMessage(null)} style={{ background: "none", border: "none", color: "#78716c", cursor: "pointer" }}>
            ✕
          </button>
        </div>
      )}

      {/* Database Statistics Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "20px" }}>
        <div className="glass-panel" style={{ padding: "20px" }}>
          <div style={{ fontSize: "0.8rem", color: "#78716c", textTransform: "uppercase", fontWeight: 700 }}>
            Total Stock Documents
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 800, color: "#1c1917", marginTop: "6px" }}>
            {stats?.totalCount?.toLocaleString() || 0}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: "20px" }}>
          <div style={{ fontSize: "0.8rem", color: "#78716c", textTransform: "uppercase", fontWeight: 700 }}>
            Active Accounts
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 800, color: "#16a34a", marginTop: "6px" }}>
            {stats?.activeCount?.toLocaleString() || 0}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: "20px" }}>
          <div style={{ fontSize: "0.8rem", color: "#78716c", textTransform: "uppercase", fontWeight: 700 }}>
            Dead / Expired Accounts
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 800, color: "#e11d48", marginTop: "6px" }}>
            {stats?.deadCount?.toLocaleString() || 0}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: "20px" }}>
          <div style={{ fontSize: "0.8rem", color: "#78716c", textTransform: "uppercase", fontWeight: 700 }}>
            Given Away Accounts
          </div>
          <div style={{ fontSize: "2rem", fontWeight: 800, color: "#0284c7", marginTop: "6px" }}>
            {stats?.givenCount?.toLocaleString() || 0}
          </div>
        </div>
      </div>

      {/* Maintenance Actions Row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "24px" }}>
        {/* Purge Dead Accounts */}
        <div className="glass-panel" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "1.4rem" }}>🗑️</span>
            <div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1c1917" }}>
                Purge Dead Stock
              </h3>
              <p style={{ fontSize: "0.82rem", color: "#78716c" }}>
                Permanently removes all cookies and combos marked as dead
              </p>
            </div>
          </div>
          <p style={{ fontSize: "0.85rem", color: "#44403c" }}>
            Currently <strong>{stats?.deadCount || 0}</strong> dead accounts are queued in the database.
          </p>
          <button
            disabled={purging || (stats?.deadCount || 0) === 0}
            onClick={() => handleAction("purge_dead", "Permanently delete all dead stock accounts?")}
            className="btn btn-danger"
            style={{ marginTop: "auto" }}
          >
            {purging ? "Purging..." : "Purge All Dead Stock"}
          </button>
        </div>

        {/* Clean Given Stock */}
        <div className="glass-panel" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "1.4rem" }}>🧹</span>
            <div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1c1917" }}>
                Clean Given Accounts
              </h3>
              <p style={{ fontSize: "0.82rem", color: "#78716c" }}>
                Removes accounts that have already been distributed to users
              </p>
            </div>
          </div>
          <p style={{ fontSize: "0.85rem", color: "#44403c" }}>
            Currently <strong>{stats?.givenCount || 0}</strong> given accounts are archived.
          </p>
          <button
            disabled={purging || (stats?.givenCount || 0) === 0}
            onClick={() => handleAction("clean_given", "Delete all previously given accounts?")}
            className="btn btn-secondary"
            style={{ marginTop: "auto" }}
          >
            Clean Given Away Accounts
          </button>
        </div>

        {/* Export Full Backup */}
        <div className="glass-panel" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontSize: "1.4rem" }}>💾</span>
            <div>
              <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1c1917" }}>
                Export Full Backup
              </h3>
              <p style={{ fontSize: "0.82rem", color: "#78716c" }}>
                Download entire stock database as formatted JSON
              </p>
            </div>
          </div>
          <p style={{ fontSize: "0.85rem", color: "#44403c" }}>
            Safely backups all {stats?.totalCount || 0} accounts, cookies, and metadata.
          </p>
          <a
            href="/api/database?action=export_backup"
            download="stock_backup.json"
            className="btn btn-primary"
            style={{ marginTop: "auto" }}
          >
            📥 Download Database JSON
          </a>
        </div>
      </div>
    </div>
  );
}
