import type { APIRoute } from "astro";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

interface TelegramUpdate {
  message?: {
    chat: { id: number };
    text?: string;
    from?: { first_name?: string; username?: string };
  };
}

export const POST: APIRoute = async ({ request }) => {
  const botToken = process.env.TG_BOT_TOKEN ?? import.meta.env.TG_BOT_TOKEN;

  console.log("[TG Webhook] Incoming request");
  console.log("[TG Webhook] Bot token present:", !!botToken);

  if (!botToken) {
    console.error(
      "[TG Webhook] No bot token in process.env or import.meta.env",
    );
    return new Response("Bot token not configured", { status: 500 });
  }

  let update: TelegramUpdate;
  try {
    update = await request.json();
    console.log("[TG Webhook] Update:", JSON.stringify(update, null, 2));
  } catch (err) {
    console.error("[TG Webhook] Invalid JSON:", err);
    return new Response("Invalid JSON", { status: 400 });
  }

  const message = update.message;
  if (!message?.text) {
    console.log("[TG Webhook] No text in message, skipping");
    return new Response("OK", { status: 200 });
  }

  const chatId = message.chat.id;
  const text = message.text.trim();
  console.log(`[TG Webhook] Chat ${chatId}, text: "${text}"`);

  if (text === "/start") {
    const firstName = message.from?.first_name || "друг";

    // Send welcome message
    console.log("[TG Webhook] Sending welcome message...");
    await sendMessage(
      botToken,
      chatId,
      [
        `Привет, <b>${escapeHtml(firstName)}</b>! 👋`,
        "",
        "Добро пожаловать в <b>Caliathletics</b> — персональные тренировки с собственным весом тела.",
        "",
        "📄 Отправляю тебе бесплатный план тренировок на неделю!",
      ].join("\n"),
    );

    // Send PDF document
    const pdfPath = join(
      process.cwd(),
      "public",
      "caliathletics-training-plan.pdf",
    );
    console.log("[TG Webhook] PDF path:", pdfPath);

    try {
      const pdfBuffer = await readFile(pdfPath);
      console.log("[TG Webhook] PDF loaded, size:", pdfBuffer.length, "bytes");

      const form = new FormData();
      form.append("chat_id", String(chatId));
      form.append(
        "document",
        new File([pdfBuffer], "caliathletics-training-plan.pdf", {
          type: "application/pdf",
        }),
      );
      form.append(
        "caption",
        "🔥 Твой план тренировок Caliathletics — начни сегодня!",
      );

      console.log("[TG Webhook] Sending document...");
      const res = await fetch(
        `https://api.telegram.org/bot${botToken}/sendDocument`,
        { method: "POST", body: form },
      );

      const resBody = await res.text();
      console.log("[TG Webhook] sendDocument response:", res.status, resBody);
    } catch (err) {
      console.error("[TG Webhook] PDF send error:", err);
    }
  }

  return new Response("OK", { status: 200 });
};

async function sendMessage(botToken: string, chatId: number, text: string) {
  const res = await fetch(
    `https://api.telegram.org/bot${botToken}/sendMessage`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: chatId, text, parse_mode: "HTML" }),
    },
  );

  const resBody = await res.text();
  console.log("[TG Webhook] sendMessage response:", res.status, resBody);
}

function escapeHtml(str: string): string {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
