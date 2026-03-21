<script lang="ts">
	import { actions } from "astro:actions";
	import { Button } from "$lib/components/ui/button";
	import * as Dialog from "$lib/components/ui/dialog";
	import { leadForm } from "../../data/content";
	import { onMount } from "svelte";

	let name = $state("");
	let contact = $state("");
	let status = $state<"idle" | "loading" | "success" | "error">("idle");
	let errorMessage = $state("");
	let open = $state(false);

	async function handleSubmit(e: Event) {
		e.preventDefault();

		if (!contact.trim()) {
			status = "error";
			errorMessage = "Укажите email, телефон или Telegram";
			setTimeout(() => { status = "idle"; }, 3000);
			return;
		}

		status = "loading";

		const { error } = await actions.submitLead({
			name: name || undefined,
			contact: contact.trim(),
		});

		if (error) {
			status = "error";
			errorMessage = error.message || "Произошла ошибка. Попробуйте позже.";
			setTimeout(() => {
				status = "idle";
			}, 3000);
			return;
		}

		status = "success";
		setTimeout(() => {
			status = "idle";
			open = false;
			name = "";
			contact = "";
		}, 2000);
	}

	onMount(() => {
		// Intercept all #contact links to open dialog directly
		document.addEventListener("click", (e) => {
			const target = (e.target as HTMLElement).closest('a[href="#contact"]');
			if (target) {
				e.preventDefault();
				open = true;
			}
		});
	});
</script>

<section id="contact" class="relative overflow-hidden py-24 sm:py-32">
	<!-- Background -->
	<div class="absolute inset-0 bg-linear-to-b from-background via-card/20 to-background"></div>
	<div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-primary/5 blur-3xl"></div>

	<div class="relative mx-auto max-w-4xl px-6 text-center">
		<!-- Header -->
		<span class="text-sm font-medium uppercase tracking-widest text-primary">Бесплатно</span>
		<h2 class="mt-4 font-display text-4xl tracking-wide sm:text-5xl md:text-6xl">
			{leadForm.title.toUpperCase()}
		</h2>
		<p class="mt-2 font-display text-3xl tracking-wide sm:text-4xl bg-linear-to-r from-brand-orange to-brand-gold bg-clip-text text-transparent">
			{leadForm.titleAccent.toUpperCase()}
		</p>
		<p class="mx-auto mt-6 max-w-lg text-lg text-muted-foreground">
			{leadForm.description}
		</p>

		<!-- CTA opens dialog -->
		<div class="mt-10">
			<Dialog.Root bind:open>
				<Dialog.Trigger
					class="inline-flex items-center gap-3 rounded-full bg-linear-to-r from-brand-orange to-brand-gold px-10 py-5 text-xl font-semibold text-background transition-all duration-300 hover:scale-105 hover:shadow-[0_0_50px_rgba(255,132,0,0.4)]"
				>
					Скачать бесплатно
					<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
					</svg>
				</Dialog.Trigger>

				<Dialog.Content class="sm:max-w-md border-border/50 bg-card/95 backdrop-blur-xl">
					<Dialog.Header>
						<Dialog.Title class="font-display text-2xl tracking-wide text-center pr-8">
							ПОЛУЧИТЬ ПЛАН ТРЕНИРОВОК
						</Dialog.Title>
						<Dialog.Description class="text-center text-muted-foreground">
							Заполните форму и получите PDF-план бесплатно
						</Dialog.Description>
					</Dialog.Header>

					<form class="mt-4 space-y-4" onsubmit={handleSubmit}>
						<div>
							<label for="dialog-name" class="mb-2 block text-sm text-muted-foreground">Имя</label>
							<input
								id="dialog-name"
								type="text"
								bind:value={name}
								placeholder="Ваше имя"
								class="w-full rounded-xl border border-border/50 bg-background/50 px-4 py-3 text-foreground placeholder:text-muted-foreground/50 transition-colors focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20"
							/>
						</div>
						<div>
							<label for="dialog-contact" class="mb-2 block text-sm text-muted-foreground">
								Email, телефон или Telegram <span class="text-primary">*</span>
							</label>
							<input
								id="dialog-contact"
								type="text"
								bind:value={contact}
								placeholder="email / +7... / @username"
								class="w-full rounded-xl border border-border/50 bg-background/50 px-4 py-3 text-foreground placeholder:text-muted-foreground/50 transition-colors focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20"
							/>
						</div>

						<Button
							type="submit"
							disabled={status === "loading" || status === "success"}
							class="mt-6! w-full rounded-xl bg-linear-to-r from-brand-orange to-brand-gold py-4 text-lg font-semibold text-background transition-all duration-300 hover:scale-[1.02] hover:shadow-[0_0_30px_rgba(255,132,0,0.3)] border-none h-auto disabled:opacity-70"
						>
							{#if status === "loading"}
								<svg class="h-5 w-5 mr-2 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
									<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
									<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
								</svg>
								Отправка...
							{:else if status === "success"}
								<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
									<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
								</svg>
								Отправлено!
							{:else if status === "error"}
								{errorMessage}
							{:else}
								{leadForm.cta}
							{/if}
						</Button>
					</form>

					<p class="mt-3 text-center text-xs text-muted-foreground/60">
						Нажимая кнопку, вы соглашаетесь с политикой конфиденциальности
					</p>
				</Dialog.Content>
			</Dialog.Root>
		</div>

		<!-- Trust indicators -->
		<div class="mt-12 flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground">
			<span class="flex items-center gap-2">
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
				</svg>
				Без спама
			</span>
			<span class="flex items-center gap-2">
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
				</svg>
				Мгновенная доставка
			</span>
			<span class="flex items-center gap-2">
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
				</svg>
				100% бесплатно
			</span>
		</div>
	</div>
</section>
