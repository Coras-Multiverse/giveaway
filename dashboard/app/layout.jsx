import "./globals.css";
import Link from "next/link";

export const metadata = {
  title: "Giveaway Command Center | Vercel Control Hub",
  description: "Enterprise Control Panel & Automation Hub for Telegram Giveaway Bot & Account Checkers",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div style={{ display: "flex", minHeight: "100vh" }}>
          {/* Sidebar */}
          <aside
            style={{
              width: "260px",
              background: "#fbf9f5",
              borderRight: "1px solid var(--border)",
              display: "flex",
              flexDirection: "column",
              flexShrink: 0,
              padding: "24px 16px",
              position: "sticky",
              top: 0,
              height: "100vh",
              boxSizing: "border-box",
            }}
          >
            {/* Logo / Brand */}
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "32px", padding: "0 8px" }}>
              <div
                style={{
                  width: "38px",
                  height: "38px",
                  borderRadius: "10px",
                  background: "linear-gradient(135deg, #f59e0b, #d97706)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontWeight: 800,
                  fontSize: "1.1rem",
                  color: "#fff",
                  boxShadow: "0 4px 14px rgba(245, 158, 11, 0.3)",
                }}
              >
                ⚡
              </div>
              <div>
                <h1 style={{ fontSize: "1.05rem", fontWeight: 800, letterSpacing: "-0.02em", color: "#1c1917" }}>
                  GIVEAWAY <span style={{ color: "#d97706" }}>PRO</span>
                </h1>
                <p style={{ fontSize: "0.7rem", color: "#78716c", fontWeight: 600 }}>CONTROL CENTER</p>
              </div>
            </div>

            {/* Navigation Links */}
            <nav style={{ display: "flex", flexDirection: "column", gap: "6px", flex: 1 }}>
              <Link
                href="/"
                className="btn-secondary"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  padding: "12px 14px",
                  borderRadius: "10px",
                  textDecoration: "none",
                  fontWeight: 600,
                  fontSize: "0.88rem",
                  transition: "all 0.2s",
                }}
              >
                <span>📊</span>
                <span>Dashboard Overview</span>
              </Link>

              <Link
                href="/stock"
                className="btn-secondary"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  padding: "12px 14px",
                  borderRadius: "10px",
                  textDecoration: "none",
                  fontWeight: 600,
                  fontSize: "0.88rem",
                }}
              >
                <span>📦</span>
                <span>Stock Management</span>
              </Link>

              <Link
                href="/giveaway"
                className="btn-secondary"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  padding: "12px 14px",
                  borderRadius: "10px",
                  textDecoration: "none",
                  fontWeight: 600,
                  fontSize: "0.88rem",
                }}
              >
                <span>🎁</span>
                <span>Giveaway Automation</span>
              </Link>

              <Link
                href="/checker"
                className="btn-secondary"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  padding: "12px 14px",
                  borderRadius: "10px",
                  textDecoration: "none",
                  fontWeight: 600,
                  fontSize: "0.88rem",
                }}
              >
                <span>🔍</span>
                <span>Live Checker Studio</span>
              </Link>

              <Link
                href="/database"
                className="btn-secondary"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  padding: "12px 14px",
                  borderRadius: "10px",
                  textDecoration: "none",
                  fontWeight: 600,
                  fontSize: "0.88rem",
                }}
              >
                <span>🗄️</span>
                <span>Database & Clean</span>
              </Link>

              <Link
                href="/settings"
                className="btn-secondary"
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  padding: "12px 14px",
                  borderRadius: "10px",
                  textDecoration: "none",
                  fontWeight: 600,
                  fontSize: "0.88rem",
                }}
              >
                <span>⚙️</span>
                <span>Bot Settings & Config</span>
              </Link>
            </nav>

            {/* Sidebar Status Footer */}
            <div
              style={{
                padding: "14px",
                borderRadius: "12px",
                background: "#f4efe6",
                border: "1px solid var(--border)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "6px" }}>
                <span style={{ fontSize: "0.75rem", color: "#78716c", fontWeight: 600 }}>System Status</span>
                <span className="badge badge-active" style={{ fontSize: "0.7rem", padding: "2px 8px" }}>
                  ONLINE
                </span>
              </div>
              <div style={{ fontSize: "0.72rem", color: "#a8a29e" }}>
                Vercel Serverless Ready (v2.0)
              </div>
            </div>
          </aside>

          {/* Main Content Area */}
          <main style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
            {/* Top Navigation Bar */}
            <header
              style={{
                height: "68px",
                background: "rgba(255, 255, 255, 0.85)",
                backdropFilter: "blur(12px)",
                borderBottom: "1px solid var(--border)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "0 32px",
                position: "sticky",
                top: 0,
                zIndex: 100,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    background: "#f4efe6",
                    padding: "6px 14px",
                    borderRadius: "9999px",
                    border: "1px solid var(--border)",
                  }}
                >
                  <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#16a34a" }} />
                  <span style={{ fontSize: "0.82rem", fontWeight: 600, color: "#44403c" }}>Connected to MongoDB</span>
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <Link href="/giveaway" className="btn btn-primary" style={{ padding: "8px 16px", fontSize: "0.82rem" }}>
                  <span>🚀</span> Trigger Quick Drop
                </Link>
                <Link href="/checker" className="btn btn-secondary" style={{ padding: "8px 14px", fontSize: "0.82rem" }}>
                  <span>⚡</span> Test Cookie
                </Link>
              </div>
            </header>

            {/* Page Children */}
            <div style={{ padding: "32px", flex: 1 }}>{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}
