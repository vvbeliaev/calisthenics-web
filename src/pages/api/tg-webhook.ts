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
  const botToken = import.meta.env.TG_BOT_TOKEN;
  if (!botToken) {
    return new Response("Bot token not configured", { status: 500 });
  }

  let update: TelegramUpdate;
  try {
    update = await request.json();
  } catch {
    return new Response("Invalid JSON", { status: 400 });
  }

  const message = update.message;
  if (!message?.text) {
    return new Response("OK", { status: 200 });
  }

  const chatId = message.chat.id;
  const text = message.text.trim();

  if (text === "/start") {
    const firstName = message.from?.first_name || "друг";

    // Send welcome message
    await sendMessage(botToken, chatId, [
      `Привет, <b>${escapeHtml(firstName)}</b>! 👋`,
      "",
      "Добро пожаловать в <b>Caliathletics</b> — персональные тренировки с собственным весом тела.",
      "",
      "📄 Отправляю тебе бесплатный план тренировок на неделю!",
    ].join("\n"));

    // Send PDF document
    const pdfPath = join(process.cwd(), "public", "caliathletics-training-plan.pdf");
    const pdfBuffer = await readFile(pdfPath);

    const form = new FormData();
    form.append("chat_id", String(chatId));
    form.append("document", new Blob([pdfBuffer], { type: "application/pdf" }), "caliathletics-training-plan.pdf");
    form.append("caption", "🔥 Твой план тренировок Caliathletics — начни сегодня!");

    const res = await fetch(`https://api.telegram.org/bot${botToken}/sendDocument`, {
      method: "POST",
      body: form,
    });

    if (!res.ok) {
      console.error("TG sendDocument error:", await res.text());
    }
  }

  return new Response("OK", { status: 200 });
};

async function sendMessage(botToken: string, chatId: number, text: string) {
  const res = await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text,
      parse_mode: "HTML",
    }),
  });

  if (!res.ok) {
    console.error("TG sendMessage error:", await res.text());
  }
}

function escapeHtml(str: string): string {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
