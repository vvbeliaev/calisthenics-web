export interface LeadData {
  name?: string;
  contact: string;
}

type ContactType = "email" | "phone" | "telegram";

function detectContactType(value: string): ContactType {
  if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return "email";
  if (/^\+?[\d\s\-()]{7,}$/.test(value.trim())) return "phone";
  return "telegram";
}

const contactLabels: Record<ContactType, string> = {
  email: "📧 Email",
  phone: "📞 Телефон",
  telegram: "💬 Telegram",
};

export async function sendLeadToTelegram(
  input: LeadData,
  botToken: string,
  chatId: string,
): Promise<void> {
  const type = detectContactType(input.contact);

  const lines: string[] = [
    "<b>🔥 Новая заявка с сайта</b>",
    "",
  ];

  if (input.name) lines.push(`<b>Имя:</b> ${escapeHtml(input.name)}`);
  lines.push(`<b>${contactLabels[type]}:</b> ${escapeHtml(input.contact)}`);
  lines.push(
    "",
    `<i>📅 ${new Date().toLocaleString("ru-RU", { timeZone: "Europe/Moscow" })}</i>`,
  );

  const text = lines.join("\n");

  const inlineKeyboard: { text: string; url: string }[][] = [];

  if (type === "telegram") {
    const handle = input.contact.replace(/^@/, "");
    inlineKeyboard.push([
      { text: "💬 Написать в Telegram", url: `https://t.me/${handle}` },
    ]);
  }

  const body: Record<string, unknown> = {
    chat_id: chatId,
    text,
    parse_mode: "HTML",
  };

  if (inlineKeyboard.length > 0) {
    body.reply_markup = { inline_keyboard: inlineKeyboard };
  }

  const res = await fetch(
    `https://api.telegram.org/bot${botToken}/sendMessage`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );

  if (!res.ok) {
    const responseBody = await res.text();
    console.error("Telegram API error:", responseBody);
    throw new Error("Не удалось отправить сообщение в Telegram");
  }
}

function escapeHtml(str: string): string {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
