<script lang="ts">
	import { Button } from "$lib/components/ui/button";
	import * as Sheet from "$lib/components/ui/sheet";

	const navLinks = [
		{ label: "Преимущества", href: "#advantages" },
		{ label: "Программа", href: "#program" },
		{ label: "Отзывы", href: "#testimonials" },
		{ label: "Каталог", href: "#catalog" },
		{ label: "FAQ", href: "#faq" },
	];

	let scrolled = $state(false);
	let mobileOpen = $state(false);

	function onScroll() {
		scrolled = window.scrollY > 50;
	}
</script>

<svelte:window onscroll={onScroll} />

<nav
	class="fixed top-0 left-0 z-50 w-full transition-all duration-500 {scrolled
		? 'bg-background/80 backdrop-blur-xl border-b border-border/50 shadow-lg shadow-black/20'
		: 'bg-transparent'}"
>
	<div class="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
		<!-- Logo -->
		<a href="/" class="flex items-center gap-3">
			<span class="font-display text-2xl tracking-wider bg-linear-to-r from-brand-orange to-brand-gold bg-clip-text text-transparent">
				CALIATHLETICS
			</span>
		</a>

		<!-- Desktop Nav -->
		<div class="hidden items-center gap-8 lg:flex">
			{#each navLinks as link}
				<a
					href={link.href}
					class="text-sm text-muted-foreground transition-colors duration-300 hover:text-primary"
				>
					{link.label}
				</a>
			{/each}
			<Button
				href="#contact"
				class="rounded-full bg-linear-to-r from-brand-orange to-brand-gold px-6 text-sm font-semibold text-background hover:shadow-[0_0_25px_rgba(255,132,0,0.35)] transition-all duration-300 hover:scale-105 border-none"
			>
				Получить программу
			</Button>
		</div>

		<!-- Mobile burger -->
		<Sheet.Root bind:open={mobileOpen}>
			<Sheet.Trigger class="lg:hidden">
				<div class="flex flex-col gap-1.5 p-2">
					<span class="block h-0.5 w-6 bg-foreground transition-transform duration-300 {mobileOpen ? 'translate-y-2 rotate-45' : ''}"></span>
					<span class="block h-0.5 w-6 bg-foreground transition-opacity duration-300 {mobileOpen ? 'opacity-0' : ''}"></span>
					<span class="block h-0.5 w-6 bg-foreground transition-transform duration-300 {mobileOpen ? '-translate-y-2 -rotate-45' : ''}"></span>
				</div>
			</Sheet.Trigger>
			<Sheet.Content side="right" class="w-80 bg-background/95 backdrop-blur-xl border-border/30">
				<Sheet.Header>
					<Sheet.Title class="font-display text-2xl tracking-wider bg-linear-to-r from-brand-orange to-brand-gold bg-clip-text text-transparent">
						CALIATHLETICS
					</Sheet.Title>
				</Sheet.Header>
				<nav class="mt-8 flex flex-col gap-6 px-2">
					{#each navLinks as link}
						<a
							href={link.href}
							class="text-lg text-muted-foreground transition-colors hover:text-primary"
							onclick={() => (mobileOpen = false)}
						>
							{link.label}
						</a>
					{/each}
					<Button
						href="#contact"
						class="mt-4 w-full rounded-full bg-linear-to-r from-brand-orange to-brand-gold text-background font-semibold border-none"
						onclick={() => (mobileOpen = false)}
					>
						Получить программу
					</Button>
				</nav>
			</Sheet.Content>
		</Sheet.Root>
	</div>
</nav>
