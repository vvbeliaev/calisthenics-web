import http from "node:http";
import { handler as astroHandler } from "./dist/server/entry.mjs";

const PORT = process.env.PORT || 4321;
const HOST = process.env.HOST || "0.0.0.0";

const server = http.createServer(astroHandler);

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
