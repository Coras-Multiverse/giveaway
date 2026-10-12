import { MongoClient } from "mongodb";
import dns from "node:dns";

let clientPromise = null;

async function buildMongoClient() {
  const rawUri = process.env.MONGO_URI ? process.env.MONGO_URI.trim() : "";
  if (!rawUri) {
    throw new Error("MONGO_URI is missing from environment variables.");
  }

  let finalUri = rawUri;

  // On Windows or environments where SRV lookup fails on local DNS, resolve replica set hosts using public DNS
  if (rawUri.startsWith("mongodb+srv://")) {
    try {
      const match = rawUri.match(/mongodb\+srv:\/\/([^@]+@)?([^/?]+)(\/[^?]*)?(\?.*)?/);
      if (match) {
        const auth = match[1] || "";
        const host = match[2];
        const pathname = match[3] || "/giveaway_bot";
        const query = match[4] || "";

        const resolver = new dns.promises.Resolver();
        resolver.setServers(["8.8.8.8", "1.1.1.1"]);
        const srvRecords = await resolver.resolveSrv(`_mongodb._tcp.${host}`);

        if (srvRecords && srvRecords.length > 0) {
          const hostsList = srvRecords.map((r) => `${r.name}:${r.port}`).join(",");
          const sep = query ? "&" : "?";
          const sslParam = query.includes("ssl=") ? "" : `${sep}ssl=true`;
          finalUri = `mongodb://${auth}${hostsList}${pathname}${query}${sslParam}`;
        }
      }
    } catch (err) {
      console.warn("SRV resolution fallback skipped:", err.message);
    }
  }

  const client = new MongoClient(finalUri);
  return await client.connect();
}

export async function getDatabase() {
  if (!clientPromise) {
    clientPromise = buildMongoClient();
  }
  const connectedClient = await clientPromise;
  return connectedClient.db("giveaway_bot");
}

export default clientPromise;
