# Hero Video Stories Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace single hero background video with 3 rotating vertical training story videos — fullscreen background on desktop, stories-style with progress bar on mobile.

**Architecture:** Single `<video>` element with JS-driven `src` swapping on `ended` event. Crossfade via opacity transition. Mobile gets a story progress bar (3 bars). Visibility/intersection-based pause for performance. Fallback to existing webp image.

**Tech Stack:** Astro 6 (`.astro` component), Tailwind CSS v4, vanilla JS (inline `<script>`)

**Spec:** `docs/superpowers/specs/2026-03-21-hero-video-stories-design.md`

---

## File Structure

- **Modify:** `src/lib/components/HeroSection.astro` — replace video markup, add story progress bar, rewrite script

---

### Task 1: Compress video files

**Files:**
- Modify: `public/vkclips_20260321070458.mp4` (in-place re-encode)
- Modify: `public/vkclips_20260321070557.mp4`
- Modify: `public/vkclips_20260321070819.mp4`

- [ ] **Step 1: Check ffmpeg is available**

Run: `ffmpeg -version | head -1`

- [ ] **Step 2: Compress all 3 videos**

```bash
for f in public/vkclips_*.mp4; do
  ffmpeg -i "$f" -c:v libx264 -crf 28 -preset slow -an -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2" -movflags +faststart "${f%.mp4}-compressed.mp4"
done
```

- [ ] **Step 3: Verify compressed sizes are under 4 MB each**

Run: `ls -lh public/vkclips_*-compressed.mp4`

- [ ] **Step 4: Replace originals with compressed versions**

```bash
for f in public/vkclips_*-compressed.mp4; do
  mv "$f" "${f%-compressed.mp4}.mp4"
done
```

- [ ] **Step 5: Verify final files**

Run: `ls -lh public/vkclips_*.mp4`
Expected: 3 files, each ~2-4 MB

---

### Task 2: Replace video markup in HeroSection

**Files:**
- Modify: `src/lib/components/HeroSection.astro`

- [ ] **Step 1: Replace the `<video>` and fallback image block**

Replace lines 9-28 (the parallax-bg div contents) with:

```astro
<div class="parallax-bg absolute inset-0">
	<!-- Single video element — src swapped by JS -->
	<video
		id="hero-video"
		muted
		playsinline
		class="absolute inset-0 h-[120%] w-full object-cover transition-opacity duration-500"
	></video>
	<!-- Fallback poster image (visible until video loads) -->
	<Image
		src={heroBg}
		alt=""
		class="absolute inset-0 h-[120%] w-full object-cover"
		widths={[800, 1200, 1920]}
		sizes="100vw"
		loading="eager"
		style="z-index: -1;"
	/>
</div>
```

- [ ] **Step 2: Verify the build compiles**

Run: `pnpm build 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add src/lib/components/HeroSection.astro
git commit -m "feat(hero): replace video element with single swappable video"
```

---

### Task 3: Add story progress bar (mobile only)

**Files:**
- Modify: `src/lib/components/HeroSection.astro`

- [ ] **Step 1: Add progress bar HTML after the film grain div (line 35) and before the Content div**

Insert after the film grain `<div>` and before `<!-- Content -->`:

```html
<!-- Story progress bar (mobile only) -->
<div id="story-progress" class="absolute top-0 left-0 right-0 z-20 flex gap-1 px-4 pt-4 md:hidden">
	<div class="story-bar h-[2px] flex-1 rounded-full bg-white/20">
		<div class="story-bar-fill h-full rounded-full bg-primary transition-none" style="width: 0%"></div>
	</div>
	<div class="story-bar h-[2px] flex-1 rounded-full bg-white/20">
		<div class="story-bar-fill h-full rounded-full bg-primary transition-none" style="width: 0%"></div>
	</div>
	<div class="story-bar h-[2px] flex-1 rounded-full bg-white/20">
		<div class="story-bar-fill h-full rounded-full bg-primary transition-none" style="width: 0%"></div>
	</div>
</div>
```

- [ ] **Step 2: Verify the build compiles**

Run: `pnpm build 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add src/lib/components/HeroSection.astro
git commit -m "feat(hero): add story progress bar for mobile"
```

---

### Task 4: Write video rotation and progress bar script

**Files:**
- Modify: `src/lib/components/HeroSection.astro`

- [ ] **Step 1: Replace the entire `<script>` block (lines 108-120) with the new script**

```html
<script>
	const VIDEO_SOURCES = [
		'/vkclips_20260321070458.mp4',
		'/vkclips_20260321070557.mp4',
		'/vkclips_20260321070819.mp4'
	];

	const video = document.getElementById('hero-video') as HTMLVideoElement;
	const heroSection = document.getElementById('hero') as HTMLElement;
	const progressBars = document.querySelectorAll('.story-bar-fill') as NodeListOf<HTMLElement>;
	const parallaxBg = document.querySelector('.parallax-bg') as HTMLElement;

	let currentIndex = 0;
	let isVisible = true;
	let isInViewport = true;

	// --- Video loading & playback ---

	function loadAndPlay(index: number) {
		currentIndex = index;
		video.src = VIDEO_SOURCES[index];
		video.load();

		const playPromise = video.play();
		if (playPromise !== undefined) {
			playPromise.catch(() => {
				// Autoplay blocked — fallback image is already visible behind video
				video.style.opacity = '0';
			});
		}
		video.style.opacity = '1';
	}

	function switchToNext() {
		// Fade out
		video.style.opacity = '0';

		// After fade completes, swap src and fade in
		setTimeout(() => {
			const nextIndex = (currentIndex + 1) % VIDEO_SOURCES.length;
			// Mark previous bar as complete
			if (progressBars[currentIndex]) {
				progressBars[currentIndex].style.width = '100%';
			}
			loadAndPlay(nextIndex);

			// Reset future bars
			for (let i = nextIndex; i < progressBars.length; i++) {
				if (i !== nextIndex) {
					progressBars[i].style.width = '0%';
				}
			}

			// If we looped back to 0, reset all bars
			if (nextIndex === 0) {
				progressBars.forEach(bar => bar.style.width = '0%');
			}
		}, 500); // matches transition-opacity duration-500
	}

	// --- Event listeners ---

	video.addEventListener('ended', switchToNext);

	video.addEventListener('timeupdate', () => {
		if (!video.duration || !isFinite(video.duration)) return;
		const progress = (video.currentTime / video.duration) * 100;
		if (progressBars[currentIndex]) {
			progressBars[currentIndex].style.width = `${progress}%`;
		}
	});

	video.addEventListener('error', () => {
		// Skip to next video on error; if all fail, fallback image shows
		const nextIndex = (currentIndex + 1) % VIDEO_SOURCES.length;
		if (nextIndex !== 0) {
			loadAndPlay(nextIndex);
		} else {
			// All videos failed — keep fallback image
			video.style.opacity = '0';
		}
	});

	// --- Visibility & intersection ---

	function pauseIfHidden() {
		if (!isVisible || !isInViewport) {
			video.pause();
		} else {
			const playPromise = video.play();
			if (playPromise !== undefined) {
				playPromise.catch(() => {});
			}
		}
	}

	document.addEventListener('visibilitychange', () => {
		isVisible = !document.hidden;
		pauseIfHidden();
	});

	const observer = new IntersectionObserver(
		(entries) => {
			isInViewport = entries[0].isIntersecting;
			pauseIfHidden();
		},
		{ threshold: 0.1 }
	);
	observer.observe(heroSection);

	// --- Parallax ---

	if (parallaxBg) {
		window.addEventListener('scroll', () => {
			const scrollY = window.scrollY;
			const heroHeight = heroSection.offsetHeight;
			if (scrollY < heroHeight) {
				parallaxBg.style.transform = `translateY(${scrollY * 0.3}px)`;
			}
		}, { passive: true });
	}

	// --- Init ---

	loadAndPlay(0);
</script>
```

- [ ] **Step 2: Verify the build compiles**

Run: `pnpm build 2>&1 | tail -5`
Expected: Build succeeds

- [ ] **Step 3: Commit**

```bash
git add src/lib/components/HeroSection.astro
git commit -m "feat(hero): add video rotation, progress bar, and visibility management"
```

---

### Task 5: Remove old video files

**Files:**
- Delete: `public/video/hero-video.mp4`
- Delete: `src/assets/video/hero-video.mp4`

- [ ] **Step 1: Verify no other files reference the old video**

Run: `grep -r "hero-video.mp4" src/` — should return no results (we already replaced it in Task 2)

- [ ] **Step 2: Delete old video files**

```bash
rm public/video/hero-video.mp4 src/assets/video/hero-video.mp4
```

- [ ] **Step 3: Remove empty video directories if no other files remain**

```bash
rmdir public/video/ 2>/dev/null; rmdir src/assets/video/ 2>/dev/null
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: remove old hero video files"
```

---

### Task 6: Manual testing

- [ ] **Step 1: Start dev server**

Run: `pnpm dev`

- [ ] **Step 2: Test desktop (≥768px)**

Open in browser. Verify:
- Video plays as fullscreen background
- At video end, crossfade transition to next video
- After 3rd video, loops back to 1st
- Text, CTA, stats all readable over gradient
- Parallax effect works on scroll
- Progress bar is NOT visible

- [ ] **Step 3: Test mobile (<768px)**

Open browser devtools, toggle mobile viewport (e.g. iPhone 14). Verify:
- Video fills screen vertically
- Story progress bar visible at top with 3 segments
- Active segment fills as video plays
- At video end, next video loads and next bar starts filling
- Previous bars show 100%
- Text and CTA readable at bottom

- [ ] **Step 4: Test fallback**

In devtools Network tab, block `*.mp4` requests. Reload. Verify:
- Fallback webp image shows
- No broken UI, no JS errors

- [ ] **Step 5: Test tab visibility**

Play video, switch to another tab, wait, switch back. Verify:
- Video pauses when tab hidden
- Video resumes when tab visible

- [ ] **Step 6: Final build check**

Run: `pnpm build 2>&1 | tail -10`
Expected: Build succeeds with no warnings
