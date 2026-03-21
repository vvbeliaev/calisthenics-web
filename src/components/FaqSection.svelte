<script lang="ts">
	import * as Accordion from "$lib/components/ui/accordion";
	import { faq } from "../data/content";
</script>

<section id="faq" class="relative overflow-hidden py-24 sm:py-32">
	<div class="absolute top-0 left-0 w-[500px] h-[500px] rounded-full bg-primary/3 blur-3xl"></div>

	<div class="relative mx-auto max-w-4xl px-6">
		<!-- Section header -->
		<div class="text-center">
			<span class="text-sm font-medium uppercase tracking-widest text-primary">FAQ</span>
			<h2 class="mt-4 font-display text-4xl tracking-wide sm:text-5xl md:text-6xl">
				ОТВЕТЫ НА ВОПРОСЫ
				<span class="bg-linear-to-r from-brand-orange to-brand-gold bg-clip-text text-transparent">
					ПО ПРОГРАММЕ!
				</span>
			</h2>
		</div>

		<!-- Accordion -->
		<div class="mt-16">
			<Accordion.Root type="single" class="space-y-4">
				{#each faq.items as item, i}
					<Accordion.Item
						value="item-{i}"
						class="rounded-xl border border-border/50 bg-card/30 px-6 backdrop-blur-sm transition-all duration-300 data-open:border-primary/30 data-open:bg-card/60 data-open:shadow-[0_0_20px_rgba(255,132,0,0.05)]"
					>
						<Accordion.Trigger
							class="flex w-full items-center justify-between py-5 text-left font-medium text-foreground transition-colors hover:text-primary [&[data-state=open]>svg]:rotate-180"
						>
							<span class="pr-4">{item.question}</span>
						</Accordion.Trigger>
						<Accordion.Content class="pb-5 text-muted-foreground leading-relaxed">
							{item.answer}
						</Accordion.Content>
					</Accordion.Item>
				{/each}
			</Accordion.Root>
		</div>
	</div>
</section>
