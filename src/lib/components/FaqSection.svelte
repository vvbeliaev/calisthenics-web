<script lang="ts">
	import * as Accordion from "$lib/components/ui/accordion";
	import { faq } from "../../data/content";
</script>

<section id="faq" class="relative overflow-hidden py-24 sm:py-32">
	<div class="absolute top-0 left-0 w-[500px] h-[500px] rounded-full bg-primary/3 blur-3xl"></div>

	<div class="relative mx-auto max-w-4xl px-6">
		<!-- Section header — left-aligned -->
		<div class="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
			<div>
				<span class="text-sm font-medium uppercase tracking-widest text-primary">FAQ</span>
				<h2 class="mt-4 font-display text-4xl tracking-wide sm:text-5xl md:text-6xl">
					ЧАСТЫЕ
					<span class="bg-linear-to-r from-brand-orange to-brand-gold bg-clip-text text-transparent">
						ВОПРОСЫ
					</span>
				</h2>
			</div>
			<p class="max-w-sm text-muted-foreground">
				Не нашли ответ? <a href="#contact" class="text-primary underline underline-offset-4 transition-colors hover:text-brand-gold">Напишите нам</a>
			</p>
		</div>

		<!-- Accordion -->
		<div class="mt-12">
			<Accordion.Root type="single" class="space-y-3">
				{#each faq.items as item, i}
					<Accordion.Item
						value="item-{i}"
						class="group rounded-xl border border-border/40 bg-card/20 backdrop-blur-sm transition-all duration-300 data-open:border-primary/30 data-open:bg-card/50 data-open:shadow-[0_0_25px_rgba(255,132,0,0.06)]"
					>
						<Accordion.Trigger
							class="flex w-full items-center gap-4 px-6 py-5 text-left font-medium text-foreground transition-colors hover:text-primary [&[data-state=open]>span.faq-num]:text-primary [&[data-state=open]>span.faq-num]:bg-primary/10 [&[data-state=open]>svg]:rotate-45"
						>
							<span class="faq-num flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-card/80 text-xs font-display text-muted-foreground transition-all duration-300">
								{String(i + 1).padStart(2, "0")}
							</span>
							<span class="flex-1 pr-4">{item.question}</span>
							<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
							</svg>
						</Accordion.Trigger>
						<Accordion.Content class="px-6 pb-5 pl-18 text-muted-foreground leading-relaxed">
							{item.answer}
						</Accordion.Content>
					</Accordion.Item>
				{/each}
			</Accordion.Root>
		</div>
	</div>
</section>
