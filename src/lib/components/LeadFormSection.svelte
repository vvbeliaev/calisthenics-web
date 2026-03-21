<script lang="ts">
  import { leadForm } from "../../data/content";
</script>

<section id="contact" class="relative overflow-hidden py-24 sm:py-32">
  <!-- Background -->
  <div
    class="absolute inset-0 bg-linear-to-b from-background via-card/20 to-background"
  ></div>
  <div
    class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-primary/5 blur-3xl"
  ></div>

  <div class="relative mx-auto max-w-5xl px-6 text-center">
    <!-- Header -->
    <span class="text-sm font-medium uppercase tracking-widest text-primary"
      >Мой подарок тебе</span
    >
    <h2
      class="mt-4 font-display text-4xl tracking-wide sm:text-5xl md:text-6xl 2xl:text-7xl"
    >
      {leadForm.title.toUpperCase()}
    </h2>
    <p
      class="mt-2 font-display text-3xl tracking-wide sm:text-4xl 2xl:text-5xl bg-linear-to-r from-brand-orange to-brand-gold bg-clip-text text-transparent"
    >
      {leadForm.titleAccent.toUpperCase()}
    </p>
    <p class="mx-auto mt-6 max-w-lg text-lg text-muted-foreground">
      {leadForm.description}
    </p>

    <!-- CTA — direct link to Telegram bot -->
    <div class="mt-10">
      <a
        href="https://t.me/vvb_CALIATHLETICS_bot"
        target="_blank"
        rel="noopener noreferrer"
        class="inline-flex items-center gap-3 rounded-full bg-linear-to-r from-brand-orange to-brand-gold px-10 py-5 text-xl font-semibold text-background transition-all duration-300 hover:scale-105 hover:shadow-[0_0_50px_rgba(255,132,0,0.4)]"
      >
        Скачать бесплатно
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-6 w-6"
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <path
            d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"
          />
        </svg>
      </a>
    </div>

    <!-- Trust indicators -->
    <div
      class="mt-12 flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground"
    >
      <span class="flex items-center gap-2">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-4 w-4 text-primary"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M5 13l4 4L19 7"
          />
        </svg>
        Без спама
      </span>
      <span class="flex items-center gap-2">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-4 w-4 text-primary"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M5 13l4 4L19 7"
          />
        </svg>
        Мгновенная доставка
      </span>
      <span class="flex items-center gap-2">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-4 w-4 text-primary"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M5 13l4 4L19 7"
          />
        </svg>
        100% бесплатно
      </span>
    </div>
  </div>
</section>
