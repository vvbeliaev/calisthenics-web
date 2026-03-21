import http from "node:http";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import sirv from "sirv";
import { handler as astroHandler } from "./dist/server/entry.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));

const PORT = process.env.PORT || 4321;
const HOST = process.env.HOST || "0.0.0.0";

const clientDir = join(__dirname, "dist", "client");

// All static files from client dir (includes _astro/*, favicon, images, video, pdf)
// ignores: false — Astro generates filenames with @ (e.g. index@_@astro.css) which
// sirv's default ignore pattern rejects
const serveStatic = sirv(clientDir, {
  ignores: false,
  maxAge: 3600,
  setHeaders(res, pathname) {
    // Hashed assets get immutable long cache
    if (pathname.startsWith("/_astro/")) {
      res.setHeader("Cache-Control", "public, max-age=31536000, immutable");
    }
  },
});

const server = http.createServer((req, res) => {
  serveStatic(req, res, () => {
    astroHandler(req, res);
  });
});

server.listen(PORT, HOST, async () => {
  console.log(`Server running on http://${HOST}:${PORT}`);
  await registerTelegramWebhook();
});

async function registerTelegramWebhook() {
  const botToken = process.env.TG_BOT_TOKEN;
  const webhookUrl = process.env.TG_WEBHOOK_URL;

  if (!botToken || !webhookUrl) {
    console.warn(
      "[TG] TG_BOT_TOKEN or TG_WEBHOOK_URL not set — skipping webhook registration",
    );
    return;
  }

  const url = `${webhookUrl}/api/tg-webhook`;

  try {
    const res = await fetch(
      `https://api.telegram.org/bot${botToken}/setWebhook`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      },
    );

    const data = await res.json();

    if (data.ok) {
      console.log(`[TG] Webhook registered: ${url}`);
    } else {
      console.error("[TG] Webhook registration failed:", data.description);
    }
  } catch (err) {
    console.error("[TG] Webhook registration error:", err.message);
  }
}
