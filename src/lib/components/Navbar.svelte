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
	class="fixed top-0 left-0 z-50 w-full transition-all duration-700 {scrolled
		? 'bg-background/70 backdrop-blur-2xl border-b border-primary/10 shadow-[0_4px_30px_rgba(0,0,0,0.4)]'
		: 'bg-transparent'}"
>
	<!-- Top accent line -->
	<div class="h-[2px] bg-linear-to-r from-transparent via-brand-orange to-transparent opacity-60"></div>

	<div class="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
		<!-- Logo -->
		<a href="/" class="group flex items-center gap-3">
			<div class="flex h-9 w-9 items-center justify-center rounded-lg border border-primary/30 bg-primary/10 transition-all duration-300 group-hover:border-primary/60 group-hover:shadow-[0_0_15px_rgba(255,132,0,0.2)]">
				<span class="font-display text-lg text-primary">C</span>
			</div>
			<span class="hidden font-display text-xl tracking-[0.25em] text-foreground sm:inline">
				CALIATHLETICS
			</span>
		</a>

		<!-- Desktop Nav -->
		<div class="hidden items-center gap-1 lg:flex">
			{#each navLinks as link, i}
				<a
					href={link.href}
					class="relative px-4 py-2 text-sm text-muted-foreground transition-all duration-300 hover:text-foreground"
				>
					<span class="relative">
						{link.label}
						<span class="absolute -bottom-1 left-0 h-px w-0 bg-primary transition-all duration-300"></span>
					</span>
				</a>
				{#if i < navLinks.length - 1}
					<span class="text-border/60 select-none">/</span>
				{/if}
			{/each}
		</div>

		<!-- CTA -->
		<div class="hidden lg:block">
			<Button
				href="#contact"
				class="rounded-full bg-linear-to-r from-brand-orange to-brand-gold px-6 py-2 text-sm font-semibold text-background border-none transition-all duration-300 hover:shadow-[0_0_25px_rgba(255,132,0,0.35)] hover:scale-105"
			>
				Записаться
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
				<nav class="mt-8 flex flex-col gap-1 px-2">
					{#each navLinks as link, i}
						<a
							href={link.href}
							class="flex items-center gap-4 rounded-lg px-3 py-3 text-muted-foreground transition-all hover:bg-primary/5 hover:text-foreground"
							onclick={() => (mobileOpen = false)}
						>
							<span class="font-display text-xs text-primary/60">0{i + 1}</span>
							<span class="text-base">{link.label}</span>
						</a>
					{/each}
					<div class="mt-6 border-t border-border/30 pt-6">
						<Button
							href="#contact"
							class="w-full rounded-full bg-linear-to-r from-brand-orange to-brand-gold text-background font-semibold border-none"
							onclick={() => (mobileOpen = false)}
						>
							Получить программу
						</Button>
					</div>
				</nav>
			</Sheet.Content>
		</Sheet.Root>
	</div>
</nav>

<style>
	a:hover span span:last-child {
		width: 100%;
	}
</style>
