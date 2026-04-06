import { defineAction, ActionError } from "astro:actions";
import { z } from "astro/zod";

import { sendLeadToTelegram } from "./tg/sendLead";

export const server = {
  submitLead: defineAction({
    accept: "json",
    input: z.object({
      name: z.string().optional(),
      contact: z.string().min(1, "Укажите email, телефон или Telegram"),
    }),
    handler: async (input) => {
      const botToken = import.meta.env.TG_BOT_TOKEN;
      const chatId = import.meta.env.TG_CHAT_ID;

      if (!botToken || !chatId) {
        throw new ActionError({
          code: "INTERNAL_SERVER_ERROR",
          message: "Telegram не настроен",
        });
      }

      try {
        await sendLeadToTelegram(input, botToken, chatId);
      } catch (e) {
        throw new ActionError({
          code: "INTERNAL_SERVER_ERROR",
          message:
            e instanceof Error ? e.message : "Не удалось отправить сообщение",
        });
      }

      return { success: true };
    },
  }),
};
