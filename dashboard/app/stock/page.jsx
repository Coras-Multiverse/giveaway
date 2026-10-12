"use client";

import { useEffect, useState } from "react";
import { getFullCountryName } from "@/lib/countries";

export default function StockPage() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("active");
  const [plan, setPlan] = useState("all");
  const [country, setCountry] = useState("all");

  // Selection
  const [selectedEmails, setSelectedEmails] = useState([]);

  // Modals
  const [showAddModal, setShowAddModal] = useState(false);
  const [showImportModal, setShowImportModal] = useState(false);

  // Form states
  const [singleForm, setSingleForm] = useState({
    email: "",
    country: "United States 🇺🇸",
    plan: "Premium",
    payment: "Visa",
    cookies: "",
    password: "",
  });

  const [bulkInput, setBulkInput] = useState("");
  const [bulkCountry, setBulkCountry] = useState("United States 🇺🇸");
  const [bulkPlan, setBulkPlan] = useState("Premium");
  const [importing, setImporting] = useState(false);

  // Notification / Alert
  const [msg, setMsg] = useState(null);

  const fetchStock = async (p = page) => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: p.toString(),
        limit: "25",
        status,
        plan,
        country,
      });
      if (search) params.set("search", search);

      const res = await fetch(`/api/stock?${params.toString()}`);
      const json = await res.json();
      if (json.success) {
        setItems(json.items);
        setTotal(json.total);
        setTotalPages(json.totalPages);
        setPage(json.page);
      }
    } catch (err) {
      console.error("Fetch stock error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStock(1);
  }, [status, plan, country]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchStock(1);
  };

  // Toggle selection
  const toggleSelectAll = () => {
    if (selectedEmails.length === items.length) {
      setSelectedEmails([]);
    } else {
      setSelectedEmails(items.map((i) => i.email));
    }
  };

  const toggleSelectOne = (email) => {
    if (selectedEmails.includes(email)) {
      setSelectedEmails(selectedEmails.filter((e) => e !== email));
    } else {
      setSelectedEmails([...selectedEmails, email]);
    }
  };

  // Delete Stock
  const deleteStock = async (email) => {
    if (!confirm(`Are you sure you want to delete ${email}?`)) return;
    try {
      const res = await fetch(`/api/stock?email=${encodeURIComponent(email)}`, { method: "DELETE" });
      const json = await res.json();
      if (json.success) {
        setMsg({ type: "success", text: "Account deleted successfully." });
        fetchStock(page);
      }
    } catch (err) {
      setMsg({ type: "error", text: err.message });
    }
  };

  // Bulk Delete
  const bulkDelete = async () => {
    if (!confirm(`Delete ${selectedEmails.length} selected account(s)?`)) return;
    try {
      const res = await fetch("/api/stock", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ emails: selectedEmails }),
      });
      const json = await res.json();
      if (json.success) {
        setSelectedEmails([]);
        setMsg({ type: "success", text: "Selected accounts deleted." });
        fetchStock(page);
      }
    } catch (err) {
      setMsg({ type: "error", text: err.message });
    }
  };

  // Add Single Stock
  const handleSingleAdd = async (e) => {
    e.preventDefault();
    if (!singleForm.email || !singleForm.cookies) {
      alert("Email and Cookies are required.");
      return;
    }
    try {
      const res = await fetch("/api/stock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(singleForm),
      });
      const json = await res.json();
      if (json.success) {
        setShowAddModal(false);
        setSingleForm({
          email: "",
          country: "United States 🇺🇸",
          plan: "Premium",
          payment: "Visa",
          cookies: "",
          password: "",
        });
        setMsg({ type: "success", text: "New account added to stock!" });
        fetchStock(1);
      }
    } catch (err) {
      alert(err.message);
    }
  };

  // Bulk Import
  const handleBulkImport = async () => {
    if (!bulkInput.trim()) return;
    try {
      setImporting(true);
      const lines = bulkInput.split("\n").filter((l) => l.trim());
      const accounts = [];

      // Check if whole text is JSON array
      if (bulkInput.trim().startsWith("[") && bulkInput.trim().endsWith("]")) {
        accounts.push({
          email: `bulk_${Date.now()}@imported.com`,
          country: bulkCountry,
          plan: bulkPlan,
          payment: "Imported",
          cookies: bulkInput.trim(),
        });
      } else {
        // Line by line combo email:password
        for (const line of lines) {
          if (line.includes(":")) {
            const [em, pw] = line.split(":", 2);
            accounts.push({
              email: em.trim(),
              password: pw ? pw.trim() : null,
              country: bulkCountry,
              plan: bulkPlan,
              payment: "Imported",
              cookies: line.trim(),
            });
          } else {
            accounts.push({
              email: `cookie_${Math.random().toString(36).substring(7)}@imported.com`,
              country: bulkCountry,
              plan: bulkPlan,
              payment: "Imported",
              cookies: line.trim(),
            });
          }
        }
      }

      const res = await fetch("/api/stock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(accounts),
      });
      const json = await res.json();
      if (json.success) {
        setShowImportModal(false);
        setBulkInput("");
        setMsg({ type: "success", text: `Imported ${json.count} accounts successfully!` });
        fetchStock(1);
      }
    } catch (err) {
      alert("Import failed: " + err.message);
    } finally {
      setImporting(false);
    }
  };

  // Export Selected as JSON
  const exportSelected = () => {
    const selectedItems = items.filter((i) => selectedEmails.includes(i.email));
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(selectedItems, null, 2));
    const dlAnchor = document.createElement("a");
    dlAnchor.setAttribute("href", dataStr);
    dlAnchor.setAttribute("download", `stock_export_${Date.now()}.json`);
    dlAnchor.click();
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px", maxWidth: "1400px", margin: "0 auto" }}>
      {/* Header and Action Buttons */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h2 style={{ fontSize: "1.75rem", fontWeight: 800, color: "#1c1917", letterSpacing: "-0.02em" }}>
            Stock Inventory Management
          </h2>
          <p style={{ color: "#78716c", fontSize: "0.9rem" }}>
            Total <strong>{total.toLocaleString()}</strong> accounts matching current filters
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          {selectedEmails.length > 0 && (
            <>
              <button onClick={bulkDelete} className="btn btn-danger">
                🗑️ Delete ({selectedEmails.length})
              </button>
              <button onClick={exportSelected} className="btn btn-secondary">
                📥 Export JSON
              </button>
            </>
          )}
          <button onClick={() => setShowImportModal(true)} className="btn btn-yellow">
            ⚡ Bulk Import
          </button>
          <button onClick={() => setShowAddModal(true)} className="btn btn-primary">
            ➕ Add Single Stock
          </button>
        </div>
      </div>

      {msg && (
        <div
          className="glass-panel"
          style={{
            padding: "14px 18px",
            borderLeft: `4px solid ${msg.type === "success" ? "#16a34a" : "#e11d48"}`,
            background: msg.type === "success" ? "#f0fdf4" : "#fef2f2",
            display: "flex",
            justifyContent: "space-between",
          }}
        >
          <span style={{ color: msg.type === "success" ? "#15803d" : "#991b1b", fontWeight: 600 }}>{msg.text}</span>
          <button onClick={() => setMsg(null)} style={{ background: "none", border: "none", color: "#78716c", cursor: "pointer" }}>
            ✕
          </button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="glass-panel" style={{ padding: "18px 24px" }}>
        <form onSubmit={handleSearchSubmit} style={{ display: "flex", gap: "12px", flexWrap: "wrap", alignItems: "center" }}>
          {/* Search Box */}
          <div style={{ flex: 1, minWidth: "220px" }}>
            <input
              type="text"
              className="input-control"
              placeholder="Search by email, country, or plan..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          {/* Status Filter */}
          <div style={{ width: "140px" }}>
            <select className="input-control" value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="given">Given Away</option>
              <option value="dead">Dead</option>
            </select>
          </div>

          {/* Plan Filter */}
          <div style={{ width: "140px" }}>
            <select className="input-control" value={plan} onChange={(e) => setPlan(e.target.value)}>
              <option value="all">All Plans</option>
              <option value="Premium">Premium</option>
              <option value="Standard">Standard</option>
              <option value="Basic">Basic</option>
              <option value="Mobile">Mobile</option>
            </select>
          </div>

          <button type="submit" className="btn btn-secondary">
            🔍 Search
          </button>
          <button
            type="button"
            onClick={() => {
              setSearch("");
              setStatus("active");
              setPlan("all");
              setCountry("all");
            }}
            className="btn btn-secondary"
          >
            Reset
          </button>
        </form>
      </div>

      {/* Stock Table */}
      <div className="glass-panel" style={{ overflow: "hidden" }}>
        {loading ? (
          <div style={{ padding: "50px", textAlign: "center", color: "#78716c" }}>
            ⏳ Loading stock records...
          </div>
        ) : items.length === 0 ? (
          <div style={{ padding: "60px", textAlign: "center", color: "#78716c" }}>
            <div style={{ fontSize: "2.5rem", marginBottom: "12px" }}>📭</div>
            <p style={{ fontSize: "1.1rem", fontWeight: 700, color: "#1c1917" }}>No accounts found</p>
            <p style={{ fontSize: "0.85rem", marginTop: "4px" }}>
              Try adjusting your filters or click "Add Single Stock" to create accounts.
            </p>
          </div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table className="custom-table">
              <thead>
                <tr>
                  <th style={{ width: "40px", textAlign: "center" }}>
                    <input
                      type="checkbox"
                      checked={selectedEmails.length === items.length && items.length > 0}
                      onChange={toggleSelectAll}
                    />
                  </th>
                  <th>Email / Account</th>
                  <th>Country (Full Name)</th>
                  <th>Plan</th>
                  <th>Payment</th>
                  <th>Status</th>
                  <th style={{ textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item._id}>
                    <td style={{ textAlign: "center" }}>
                      <input
                        type="checkbox"
                        checked={selectedEmails.includes(item.email)}
                        onChange={() => toggleSelectOne(item.email)}
                      />
                    </td>
                    <td>
                      <div style={{ fontWeight: 600, color: "#1c1917" }}>{item.email}</div>
                      {item.password && (
                        <div style={{ fontSize: "0.75rem", color: "#78716c" }}>Pass: {item.password}</div>
                      )}
                    </td>
                    <td style={{ fontWeight: 600, color: "#44403c" }}>
                      {getFullCountryName(item.country)}
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          item.plan?.includes("Premium")
                            ? "badge-plan-premium"
                            : item.plan?.includes("Standard")
                            ? "badge-plan-standard"
                            : "badge-plan-basic"
                        }`}
                      >
                        {item.plan || "N/A"}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: "0.82rem", color: "#57534e" }}>{item.payment || "N/A"}</span>
                    </td>
                    <td>
                      <span className={`badge ${item.status === "active" ? "badge-active" : "badge-dead"}`}>
                        {item.status || "active"}
                      </span>
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <div style={{ display: "inline-flex", gap: "6px" }}>
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(item.cookies || "");
                            alert("Cookies copied to clipboard!");
                          }}
                          className="btn btn-secondary"
                          style={{ padding: "5px 10px", fontSize: "0.75rem" }}
                          title="Copy Cookies"
                        >
                          📋
                        </button>
                        <button
                          onClick={() => deleteStock(item.email)}
                          className="btn btn-danger"
                          style={{ padding: "5px 10px", fontSize: "0.75rem" }}
                          title="Delete"
                        >
                          🗑️
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        {totalPages > 1 && (
          <div
            style={{
              padding: "16px 24px",
              background: "#faf8f5",
              borderTop: "1px solid var(--border)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span style={{ fontSize: "0.85rem", color: "#78716c", fontWeight: 600 }}>
              Page {page} of {totalPages}
            </span>
            <div style={{ display: "flex", gap: "8px" }}>
              <button
                disabled={page <= 1}
                onClick={() => fetchStock(page - 1)}
                className="btn btn-secondary"
                style={{ padding: "6px 14px", fontSize: "0.82rem" }}
              >
                Previous
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => fetchStock(page + 1)}
                className="btn btn-secondary"
                style={{ padding: "6px 14px", fontSize: "0.82rem" }}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Add Single Stock Modal */}
      {showAddModal && (
        <div className="modal-overlay">
          <div className="glass-panel" style={{ width: "500px", padding: "28px" }}>
            <h3 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "16px", color: "#1c1917" }}>
              ➕ Add Single Stock Account
            </h3>
            <form onSubmit={handleSingleAdd} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div>
                <label style={{ fontSize: "0.8rem", color: "#78716c", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                  Account Email
                </label>
                <input
                  type="text"
                  required
                  className="input-control"
                  placeholder="user@example.com"
                  value={singleForm.email}
                  onChange={(e) => setSingleForm({ ...singleForm, email: e.target.value })}
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div>
                  <label style={{ fontSize: "0.8rem", color: "#78716c", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                    Country Full Name
                  </label>
                  <input
                    type="text"
                    className="input-control"
                    value={singleForm.country}
                    onChange={(e) => setSingleForm({ ...singleForm, country: e.target.value })}
                  />
                </div>
                <div>
                  <label style={{ fontSize: "0.8rem", color: "#78716c", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                    Plan
                  </label>
                  <select
                    className="input-control"
                    value={singleForm.plan}
                    onChange={(e) => setSingleForm({ ...singleForm, plan: e.target.value })}
                  >
                    <option value="Premium">Premium</option>
                    <option value="Standard">Standard</option>
                    <option value="Basic">Basic</option>
                    <option value="Mobile">Mobile</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ fontSize: "0.8rem", color: "#78716c", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                  Cookies (Netscape or JSON string)
                </label>
                <textarea
                  required
                  rows={5}
                  className="input-control"
                  placeholder="Paste Netscape tab-separated lines or JSON array..."
                  value={singleForm.cookies}
                  onChange={(e) => setSingleForm({ ...singleForm, cookies: e.target.value })}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "10px" }}>
                <button type="button" onClick={() => setShowAddModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Bulk Import Modal */}
      {showImportModal && (
        <div className="modal-overlay">
          <div className="glass-panel" style={{ width: "600px", padding: "28px" }}>
            <h3 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "16px", color: "#1c1917" }}>
              ⚡ Bulk Import Accounts & Combos
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div>
                  <label style={{ fontSize: "0.8rem", color: "#78716c", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                    Default Country
                  </label>
                  <input
                    type="text"
                    className="input-control"
                    value={bulkCountry}
                    onChange={(e) => setBulkCountry(e.target.value)}
                  />
                </div>
                <div>
                  <label style={{ fontSize: "0.8rem", color: "#78716c", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                    Default Plan
                  </label>
                  <select
                    className="input-control"
                    value={bulkPlan}
                    onChange={(e) => setBulkPlan(e.target.value)}
                  >
                    <option value="Premium">Premium</option>
                    <option value="Standard">Standard</option>
                    <option value="Basic">Basic</option>
                    <option value="Mobile">Mobile</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ fontSize: "0.8rem", color: "#78716c", fontWeight: 600, display: "block", marginBottom: "4px" }}>
                  Input (Paste lines of email:password combos, Netscape blocks, or JSON)
                </label>
                <textarea
                  rows={8}
                  className="input-control"
                  placeholder="email1:pass1&#10;email2:pass2&#10;or full cookie string..."
                  value={bulkInput}
                  onChange={(e) => setBulkInput(e.target.value)}
                />
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "10px" }}>
                <button
                  type="button"
                  disabled={importing}
                  onClick={() => setShowImportModal(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={importing || !bulkInput.trim()}
                  onClick={handleBulkImport}
                  className="btn btn-primary"
                >
                  {importing ? "Importing..." : "Process Import"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
