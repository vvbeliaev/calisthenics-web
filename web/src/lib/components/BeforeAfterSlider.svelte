<script lang="ts">
	let {
		beforeSrc,
		afterSrc,
		beforeAlt = 'До',
		afterAlt = 'После',
		beforeLabel = 'До',
		afterLabel = 'После',
	}: {
		beforeSrc: string;
		afterSrc: string;
		beforeAlt?: string;
		afterAlt?: string;
		beforeLabel?: string;
		afterLabel?: string;
	} = $props();

	let containerEl: HTMLDivElement | undefined = $state();
	let position = $state(50);
	let isDragging = $state(false);
	let isHovering = $state(false);

	function getPosition(e: MouseEvent | Touch) {
		if (!containerEl) return 50;
		const rect = containerEl.getBoundingClientRect();
		const x = ('clientX' in e ? e.clientX : e.clientX) - rect.left;
		return Math.max(0, Math.min(100, (x / rect.width) * 100));
	}

	function onPointerDown(e: PointerEvent) {
		isDragging = true;
		position = getPosition(e);
		(e.target as HTMLElement)?.setPointerCapture?.(e.pointerId);
	}

	function onPointerMove(e: PointerEvent) {
		if (!isDragging) return;
		e.preventDefault();
		position = getPosition(e);
	}

	function onPointerUp() {
		isDragging = false;
	}
</script>

<div
	class="before-after-slider group"
	class:is-dragging={isDragging}
	bind:this={containerEl}
	onpointerdown={onPointerDown}
	onpointermove={onPointerMove}
	onpointerup={onPointerUp}
	onpointercancel={onPointerUp}
	onmouseenter={() => (isHovering = true)}
	onmouseleave={() => { isHovering = false; isDragging = false; }}
	role="slider"
	aria-label="Сравнение до и после"
	aria-valuenow={Math.round(position)}
	aria-valuemin={0}
	aria-valuemax={100}
	tabindex="0"
	onkeydown={(e) => {
		if (e.key === 'ArrowLeft') position = Math.max(0, position - 2);
		if (e.key === 'ArrowRight') position = Math.min(100, position + 2);
	}}
>
	<!-- After image (full, background layer) -->
	<img
		src={afterSrc}
		alt={afterAlt}
		class="slider-img"
		draggable="false"
	/>

	<!-- Before image (clipped) -->
	<div
		class="before-layer"
		style="clip-path: inset(0 {100 - position}% 0 0);"
	>
		<img
			src={beforeSrc}
			alt={beforeAlt}
			class="slider-img"
			draggable="false"
		/>
	</div>

	<!-- Divider line -->
	<div
		class="divider-line"
		style="left: {position}%;"
	>
		<div class="divider-track"></div>

		<!-- Handle -->
		<div class="divider-handle" class:active={isDragging || isHovering}>
			<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
				<path d="M8 5L3 12L8 19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
				<path d="M16 5L21 12L16 19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
			</svg>
		</div>
	</div>

	<!-- Labels -->
	<span
		class="slider-label label-before"
		class:label-hidden={position < 15}
	>
		{beforeLabel}
	</span>
	<span
		class="slider-label label-after"
		class:label-hidden={position > 85}
	>
		{afterLabel}
	</span>
</div>

<style>
	.before-after-slider {
		position: relative;
		overflow: hidden;
		border-radius: 1rem;
		cursor: ew-resize;
		touch-action: pan-y;
		user-select: none;
		aspect-ratio: 3/4;
		border: 1px solid oklch(1 0 0 / 8%);
		transition: border-color 0.3s ease;
	}

	.before-after-slider:hover,
	.before-after-slider:focus-visible {
		border-color: oklch(0.72 0.19 55 / 40%);
		outline: none;
	}

	.slider-img {
		display: block;
		width: 100%;
		height: 100%;
		object-fit: cover;
		pointer-events: none;
	}

	.before-layer {
		position: absolute;
		inset: 0;
		z-index: 1;
	}

	.before-layer img {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
	}

	.divider-line {
		position: absolute;
		top: 0;
		bottom: 0;
		z-index: 2;
		transform: translateX(-50%);
		pointer-events: none;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.divider-track {
		position: absolute;
		top: 0;
		bottom: 0;
		width: 2px;
		background: linear-gradient(
			180deg,
			transparent 0%,
			oklch(0.72 0.19 55) 15%,
			oklch(0.88 0.17 90) 50%,
			oklch(0.72 0.19 55) 85%,
			transparent 100%
		);
		box-shadow:
			0 0 8px oklch(0.72 0.19 55 / 50%),
			0 0 20px oklch(0.72 0.19 55 / 20%);
	}

	.divider-handle {
		position: relative;
		z-index: 3;
		width: 44px;
		height: 44px;
		border-radius: 50%;
		background: oklch(0.17 0.01 175 / 90%);
		border: 2px solid oklch(0.72 0.19 55);
		display: flex;
		align-items: center;
		justify-content: center;
		color: oklch(0.88 0.17 90);
		transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
		box-shadow:
			0 0 12px oklch(0.72 0.19 55 / 30%),
			0 2px 8px oklch(0 0 0 / 40%);
		backdrop-filter: blur(8px);
	}

	.divider-handle.active {
		transform: scale(1.12);
		border-color: oklch(0.88 0.17 90);
		box-shadow:
			0 0 20px oklch(0.72 0.19 55 / 50%),
			0 0 40px oklch(0.88 0.17 90 / 20%),
			0 2px 8px oklch(0 0 0 / 40%);
	}

	.is-dragging {
		cursor: grabbing;
	}

	.slider-label {
		position: absolute;
		bottom: 0.75rem;
		z-index: 3;
		padding: 0.25rem 0.75rem;
		border-radius: 9999px;
		font-size: 0.7rem;
		font-weight: 600;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		backdrop-filter: blur(8px);
		pointer-events: none;
		transition: opacity 0.25s ease, transform 0.25s ease;
	}

	.label-before {
		left: 0.75rem;
		background: oklch(0.17 0.01 175 / 80%);
		color: oklch(0.65 0 0);
		border: 1px solid oklch(1 0 0 / 10%);
	}

	.label-after {
		right: 0.75rem;
		background: oklch(0.72 0.19 55 / 90%);
		color: oklch(0.13 0.01 175);
		border: 1px solid oklch(0.88 0.17 90 / 30%);
	}

	.label-hidden {
		opacity: 0;
		transform: scale(0.9);
	}
</style>
