/**
 * Translates localized or corrupted Netflix plans into clean standard English tiers.
 */
export function standardizePlan(rawPlan, standardPlan) {
  if (standardPlan && standardPlan !== "N/A" && standardPlan !== "Unknown" && standardPlan !== "") {
    const sp = String(standardPlan).trim();
    if (["Premium", "Standard", "Basic", "Mobile"].includes(sp)) {
      return sp;
    }
  }
  if (!rawPlan) return "Premium";
  const p = String(rawPlan).toLowerCase();
  if (p.includes("error") || p.includes("500") || p.includes("server error")) {
    return "Premium";
  }
  if (p.includes("premium") || p.includes("prémium") || p.includes("pre") || p.includes("4k") || p.includes("ultra")) {
    return "Premium";
  }
  if (p.includes("standard") || p.includes("estándar") || p.includes("padrão") || p.includes("standart") || p.includes("hd") || p.includes("1080")) {
    return "Standard";
  }
  if (p.includes("basic") || p.includes("básico") || p.includes("basique") || p.includes("basico") || p.includes("720")) {
    return "Basic";
  }
  if (p.includes("mobile") || p.includes("móvil") || p.includes("mobil")) {
    return "Mobile";
  }
  return "Premium";
}
