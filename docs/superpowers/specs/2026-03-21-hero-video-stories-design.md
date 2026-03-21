# Hero секция: 3 видео-сторис тренера

## Контекст

Есть 3 вертикальных видео (9:16) из VK Clips с тренировками эксперта:
- `vkclips_20260321070458.mp4` (10.6 MB)
- `vkclips_20260321070557.mp4` (18.0 MB)
- `vkclips_20260321070819.mp4` (6.8 MB)

Нужно заменить текущий `hero-video.mp4` на эти 3 видео. Воспроизведение без звука, autoplay, loop через все 3.

**Важно:** перед использованием видео необходимо сжать (ffmpeg, H.264, CRF 28) до ~2-4 MB каждое. Итоговый бюджет — не более 12 MB на все 3 видео.

## Решение

Адаптивный hero с двумя принципиально разными подходами для десктопа и мобилки.

### Десктоп (≥768px): Fullscreen фон + автосмена

- Одно видео растянуто на весь фон hero через `object-fit: cover` (обрезает бока вертикального видео, показывая центральную часть)
- Два затемняющих градиента (сохраняем текущую структуру):
  1. Снизу вверх: `rgba(6,16,15,0.9)` → `transparent` (читаемость статистики)
  2. Слева направо: `rgba(6,16,15,0.95)` → `rgba(6,16,15,0.2)` (читаемость текста)
- Автосмена по событию `ended` — когда текущее видео заканчивается, crossfade на следующее (transition opacity ~1s). Не используем `setInterval` — привязка к реальной длительности видео
- Сохраняется film grain overlay и параллакс-эффект из текущей реализации
- Контент (заголовок, описание, CTA, статистика) без изменений, позиционирован слева

### Мобилка (<768px): Fullscreen сторис

- Видео занимает весь экран hero (вертикальный формат = нативно подходит)
- `object-fit: cover` на полный viewport
- Story progress bar сверху — 3 полоски, активная заполняется по мере проигрывания текущего видео
- Градиент снизу вверх: `rgba(6,16,15,0.95)` → `transparent` — текст и CTA внизу экрана
- Автосмена по окончании каждого видео (событие `ended`)
- После последнего — loop на первое
- Тап-навигация: вне скоупа первой итерации (только автосмена)

## Техническая реализация

### Архитектура: один `<video>` элемент

Используем **один** `<video>` элемент и меняем `src` при переключении. Это решает проблему памяти на мобильных устройствах (некоторые браузеры позволяют только одно активное видео).

```html
<div class="hero-video-container">
  <video id="hero-video" class="hero-video" muted playsinline autoplay></video>
</div>
```

Массив источников в JS:
```js
const videos = [
  '/vkclips_20260321070458.mp4',
  '/vkclips_20260321070557.mp4',
  '/vkclips_20260321070819.mp4'
];
```

### Логика смены видео (inline `<script>`)

```
- Один <video> элемент, массив src
- currentIndex = 0
- При загрузке: src = videos[0], play()
- Слушаем событие `ended` → fadeOut (opacity 0, transition 0.5s) → по transitionend меняем src → fadeIn (opacity 1)
- После последнего видео — loop на videos[0]
- Обработка play() rejection: если play() выбрасывает ошибку → показываем fallback-картинку
- visibilitychange: при скрытии вкладки — pause(), при возврате — play()
- IntersectionObserver: когда hero выходит из viewport — pause(), входит — play()
```

### Story Progress Bar (только мобилка)

```html
<div class="story-progress"> <!-- hidden на десктопе через md:hidden -->
  <div class="story-bar">
    <div class="story-bar-fill"></div>
  </div>
  <div class="story-bar">
    <div class="story-bar-fill"></div>
  </div>
  <div class="story-bar">
    <div class="story-bar-fill"></div>
  </div>
</div>
```

Стилизация:
- Контейнер: `flex gap-1 px-4 pt-4` абсолютно позиционирован сверху, z-index поверх видео
- Каждый bar: `h-[2px] flex-1 rounded-full bg-white/20`
- Fill: `h-full rounded-full bg-brand-orange`, ширина обновляется через JS
- Обновление ширины: `timeupdate` → `width = (currentTime / duration) * 100%`, с guard на `NaN`/`Infinity` (до загрузки metadata `duration` может быть невалидным — ставим 0%)
- Пройденные бары: fill = 100%, будущие = 0%

### CSS

```css
.hero-video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 120%; /* для параллакса */
  object-fit: cover;
  transition: opacity 0.5s ease;
}
```

### Обработка ошибок

- **play() rejection** (блокировка автовоспроизведения, режим экономии): показываем fallback `hero-background.webp` через Astro Image (уже реализовано в текущем коде)
- **Ошибка загрузки видео** (`error` event): пропускаем на следующее видео. Если все 3 не загрузились — показываем fallback-картинку
- **duration = NaN**: progress bar fill ставим в 0% до получения валидного значения через `loadedmetadata`

### Пауза при невидимости

- `document.addEventListener('visibilitychange')`: при `hidden` — `video.pause()`, при `visible` — `video.play()`
- `IntersectionObserver` на hero-контейнере (threshold: 0.1): при выходе из viewport — `pause()`, при входе — `play()`. Это экономит ресурсы когда пользователь проскроллил ниже

### Оптимизация производительности

- Один `<video>` элемент вместо трёх — минимальное потребление памяти
- Видео сжаты до ~2-4 MB каждое (H.264, CRF 28)
- Fallback: webp-картинка `hero-background.webp` (уже есть в проекте)
- Параллакс через `transform: translateY()` (GPU-ускорение, без layout thrashing)
- `will-change: transform` на видео-контейнере (для параллакса)

### Файлы видео

Видео остаются в `public/` (уже там). Переименовывать не нужно. Старый `public/video/hero-video.mp4` и `src/assets/video/hero-video.mp4` удаляем после замены.

## Что НЕ меняется

- Весь текстовый контент hero (заголовок, описание, CTA)
- Статистика внизу (600+ клиентов, 5+ лет, 4 дня/неделю)
- Scroll indicator с bounce-анимацией
- Навигационные ссылки
- Film grain overlay (SVG noise texture)
- Два градиентных оверлея (адаптируем значения, сохраняем структуру двух слоёв)
- Fallback-картинка `hero-background.webp` через Astro Image

## Acceptance Criteria

1. На десктопе: видео автоматически проигрывается как фон, при окончании плавно (crossfade) переходит к следующему, после 3-го — loop на 1-е
2. На мобилке: видео полноэкранное, story progress bar показывает прогресс текущего видео и какое видео активно
3. При блокировке autoplay браузером — отображается fallback webp-картинка
4. При скрытии вкладки или скролле мимо hero — видео ставится на паузу
5. LCP hero-секции не ухудшается (fallback-картинка грузится сразу, видео — lazy)
6. Нет layout shift при загрузке видео (контейнер имеет фиксированные размеры)
7. Работает в Chrome, Safari, Firefox (последние 2 версии)

## Затрагиваемые файлы

1. `src/lib/components/HeroSection.astro` — основные изменения (HTML + CSS + JS)
2. Удаление: `public/video/hero-video.mp4`, `src/assets/video/hero-video.mp4`
