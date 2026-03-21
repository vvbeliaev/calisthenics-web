<script lang="ts">
	import { Button } from "$lib/components/ui/button";
	import { leadForm } from "../data/content";

	let name = $state("");
	let email = $state("");
	let phone = $state("");
	let submitted = $state(false);

	function handleSubmit(e: Event) {
		e.preventDefault();
		// In production, this would send to an API
		submitted = true;
		setTimeout(() => (submitted = false), 3000);
	}
</script>

<section id="contact" class="relative overflow-hidden py-24 sm:py-32">
	<!-- Background -->
	<div class="absolute inset-0 bg-gradient-to-b from-background via-card/30 to-background"></div>
	<div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-primary/5 blur-3xl"></div>

	<div class="relative mx-auto max-w-3xl px-6">
		<div class="rounded-3xl border border-border/50 bg-card/50 p-8 backdrop-blur-sm sm:p-12">
			<!-- Header -->
			<div class="text-center">
				<span class="text-sm font-medium uppercase tracking-widest text-primary">Бесплатно</span>
				<h2 class="mt-4 font-display text-4xl tracking-wide sm:text-5xl">
					{leadForm.title.toUpperCase()}
				</h2>
				<p class="mt-2 font-display text-3xl tracking-wide sm:text-4xl bg-linear-to-r from-brand-orange to-brand-gold bg-clip-text text-transparent">
					{leadForm.titleAccent.toUpperCase()}
				</p>
				<p class="mx-auto mt-6 max-w-md text-muted-foreground">
					{leadForm.description}
				</p>
			</div>

			<!-- Form -->
			<form class="mt-10 space-y-4" onsubmit={handleSubmit}>
				<div>
					<label for="name" class="mb-2 block text-sm text-muted-foreground">Имя</label>
					<input
						id="name"
						type="text"
						bind:value={name}
						placeholder="Ваше имя"
						required
						class="w-full rounded-xl border border-border/50 bg-background/50 px-4 py-3 text-foreground placeholder:text-muted-foreground/50 transition-colors focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20"
					/>
				</div>
				<div>
					<label for="email" class="mb-2 block text-sm text-muted-foreground">Email</label>
					<input
						id="email"
						type="email"
						bind:value={email}
						placeholder="your@email.com"
						required
						class="w-full rounded-xl border border-border/50 bg-background/50 px-4 py-3 text-foreground placeholder:text-muted-foreground/50 transition-colors focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20"
					/>
				</div>
				<div>
					<label for="phone" class="mb-2 block text-sm text-muted-foreground">Телефон</label>
					<input
						id="phone"
						type="tel"
						bind:value={phone}
						placeholder="+7 (___) ___-__-__"
						class="w-full rounded-xl border border-border/50 bg-background/50 px-4 py-3 text-foreground placeholder:text-muted-foreground/50 transition-colors focus:border-primary/50 focus:outline-none focus:ring-2 focus:ring-primary/20"
					/>
				</div>

				<Button
					type="submit"
					class="!mt-6 w-full rounded-xl bg-linear-to-r from-brand-orange to-brand-gold py-4 text-lg font-semibold text-background transition-all duration-300 hover:scale-[1.02] hover:shadow-[0_0_30px_rgba(255,132,0,0.3)] border-none h-auto"
				>
					{#if submitted}
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
						</svg>
						Отправлено!
					{:else}
						{leadForm.cta}
					{/if}
				</Button>
			</form>

			<p class="mt-4 text-center text-xs text-muted-foreground/60">
				Нажимая кнопку, вы соглашаетесь с политикой конфиденциальности
			</p>
		</div>
	</div>
</section>
