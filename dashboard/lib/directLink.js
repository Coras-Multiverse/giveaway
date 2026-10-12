import crypto from "crypto";

function getRandomChars(chars, len) {
  let res = "";
  for (let i = 0; i < len; i++) {
    res += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return res;
}

function getRandomEsn() {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  return `NFAPPL-02-IPHONE8%3D1-PXA-${getRandomChars(chars, 120)}`;
}

function getRandomGuid() {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  return getRandomChars(chars, 24);
}

export function parseCookiesToHeader(cookiesRaw) {
  if (!cookiesRaw) return "";
  let cookieMap = new Map();

  // If already a JSON string
  if (typeof cookiesRaw === "string" && (cookiesRaw.trim().startsWith("[") || cookiesRaw.trim().startsWith("{"))) {
    try {
      const parsed = JSON.parse(cookiesRaw);
      const list = Array.isArray(parsed) ? parsed : [parsed];
      for (const c of list) {
        const name = c.name || c.Name;
        const val = c.value || c.Value;
        if (name && val && !cookieMap.has(name)) {
          cookieMap.set(name, decodeURIComponent(val));
        }
      }
    } catch {
      // fallback to Netscape/string parsing
    }
  }

  // Netscape / Tab-separated / Name=Value string parsing
  if (cookieMap.size === 0 && typeof cookiesRaw === "string") {
    const lines = cookiesRaw.split("\n");
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;

      const tabs = trimmed.split("\t");
      if (tabs.length >= 7) {
        const name = tabs[5]?.trim();
        const val = tabs[6]?.trim();
        if (name && val && !cookieMap.has(name)) {
          cookieMap.set(name, val);
        }
      } else if (trimmed.includes("=")) {
        const parts = trimmed.split(";");
        for (const p of parts) {
          const eqIdx = p.indexOf("=");
          if (eqIdx !== -1) {
            const name = p.slice(0, eqIdx).trim();
            const val = p.slice(eqIdx + 1).trim();
            if (name && val && !cookieMap.has(name)) {
              cookieMap.set(name, val);
            }
          }
        }
      }
    }
  }

  const parts = [];
  for (const [name, val] of cookieMap.entries()) {
    parts.push(`${name}=${val}`);
  }
  return parts.join("; ");
}

/**
 * Generate direct login link using Netflix iOS API from cookies.
 */
export async function generateDirectLoginLink(cookiesRaw) {
  try {
    const cookieHeader = parseCookiesToHeader(cookiesRaw);
    if (!cookieHeader || !cookieHeader.includes("NetflixId")) {
      return null;
    }

    const guid = getRandomGuid();
    const topUuid = crypto.randomUUID().toUpperCase();
    const esn = getRandomEsn();

    const params = new URLSearchParams({
      appVersion: "15.48.1",
      config: JSON.stringify({
        gamesInTrailersEnabled: "false",
        isTrailersEvidenceEnabled: "false",
        cdsMyListSortEnabled: "true",
        kidsBillboardEnabled: "true",
        addHorizontalBoxArtToVideoSummariesEnabled: "false",
        skOverlayTestEnabled: "false",
        homeFeedTestTVMovieListsEnabled: "false",
        baselineOnIpadEnabled: "true",
        trailersVideoIdLoggingFixEnabled: "true",
        postPlayPreviewsEnabled: "false",
        bypassContextualAssetsEnabled: "false",
        roarEnabled: "false",
        useSeason1AltLabelEnabled: "false",
        disableCDSSearchPaginationSectionKinds: ["searchVideoCarousel"],
        cdsSearchHorizontalPaginationEnabled: "true",
        searchPreQueryGamesEnabled: "true",
        kidsMyListEnabled: "true",
        billboardEnabled: "true",
        useCDSGalleryEnabled: "true",
        contentWarningEnabled: "true",
        videosInPopularGamesEnabled: "true",
        avifFormatEnabled: "false",
        sharksEnabled: "true",
      }),
      device_type: "NFAPPL-02-",
      esn: esn,
      idiom: "phone",
      iosVersion: "15.8.5",
      isTablet: "false",
      languages: "en-US",
      locale: "en-US",
      maxDeviceWidth: "375",
      model: "saget",
      modelType: "IPHONE8-1",
      odpAware: "true",
      path: '["account","token","default"]',
      pathFormat: "graph",
      pixelDensity: "2.0",
      progressive: "false",
      responseFormat: "json",
    });

    const headers = {
      "User-Agent": "Argo/15.48.1 (iPhone; iOS 15.8.5; Scale/2.00)",
      "x-netflix.request.attempt": "1",
      "x-netflix.request.client.user.guid": guid,
      "x-netflix.context.profile-guid": guid,
      "x-netflix.request.routing": '{"path":"/nq/mobile/nqios/~15.48.0/user","control_tag":"iosui_argo"}',
      "x-netflix.context.app-version": "15.48.1",
      "x-netflix.argo.translated": "true",
      "x-netflix.context.form-factor": "phone",
      "x-netflix.context.sdk-version": "2012.4",
      "x-netflix.client.appversion": "15.48.1",
      "x-netflix.context.max-device-width": "375",
      "x-netflix.tracing.cl.useractionid": crypto.randomUUID().toUpperCase(),
      "x-netflix.client.type": "argo",
      "x-netflix.client.ftl.esn": esn.replace("%3D", "="),
      "x-netflix.context.locales": "en-US",
      "x-netflix.context.top-level-uuid": topUuid,
      "x-netflix.client.iosversion": "15.8.5",
      "accept-language": "en-US;q=1",
      "x-netflix.context.os-version": "15.8.5",
      "x-netflix.request.client.context": '{"appState":"foreground"}',
      "x-netflix.context.ui-flavor": "argo",
      "x-netflix.argo.nfnsm": "9",
      "x-netflix.context.pixel-density": "2.0",
      "x-netflix.request.toplevel.uuid": topUuid,
      Cookie: cookieHeader,
    };

    const apiUrl = `https://ios.prod.ftl.netflix.com/iosui/user/latest?${params.toString()}`;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 12000);

    const res = await fetch(apiUrl, {
      method: "GET",
      headers,
      signal: controller.signal,
    });
    clearTimeout(timeout);

    if (!res.ok) {
      return null;
    }

    const data = await res.json();
    const token = data?.value?.account?.token?.default?.token;
    if (token) {
      return `https://netflix.com/?nftoken=${encodeURIComponent(token)}`;
    }
  } catch (err) {
    console.error("Direct link generation error:", err.message);
  }
  return null;
}
