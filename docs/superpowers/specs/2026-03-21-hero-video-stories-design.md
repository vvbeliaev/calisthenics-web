# Hero секция: 3 видео-сторис тренера

## Контекст

Есть 3 вертикальных видео (9:16) из VK Clips с тренировками эксперта:
- `vkclips_20260321070458.mp4` (10.6 MB)
- `vkclips_20260321070557.mp4` (18.0 MB)
- `vkclips_20260321070819.mp4` (6.8 MB)

Нужно заменить текущий `hero-video.mp4` на эти 3 видео. Воспроизведение без звука, autoplay, loop через все 3.

## Решение

Адаптивный hero с двумя принципиально разными подходами для десктопа и мобилки.

### Десктоп (≥768px): Fullscreen фон + автосмена

- Одно видео растянуто на весь фон hero через `object-fit: cover` (обрезает бока вертикального видео, показывая центральную часть)
- Затемняющий градиент слева направо: `rgba(6,16,15,0.95)` → `rgba(6,16,15,0.2)` — текст читаем слева, видео проглядывает справа
- Каждые ~10 секунд видео плавно сменяется crossfade-переходом (opacity transition ~1s)
- Сохраняется film grain overlay и параллакс-эффект из текущей реализации
- Контент (заголовок, описание, CTA, статистика) без изменений, позиционирован слева

### Мобилка (<768px): Fullscreen сторис

- Видео занимает весь экран hero (вертикальный формат = нативно подходит)
- `object-fit: cover` на полный viewport
- Story progress bar сверху — 3 полоски, активная заполняется по мере проигрывания текущего видео
- Градиент снизу вверх: `rgba(6,16,15,0.95)` → `transparent` — текст и CTA внизу экрана
- Автосмена по окончании каждого видео (событие `ended`)
- После последнего — loop на первое

## Техническая реализация

### Компонент: HeroSection.astro

Заменяем один `<video>` на 3 элемента `<video>` с абсолютным позиционированием:

```html
<div class="hero-video-container">
  <video class="hero-video active" src="/vkclips_20260321070458.mp4" muted playsinline autoplay></video>
  <video class="hero-video" src="/vkclips_20260321070557.mp4" muted playsinline preload="metadata"></video>
  <video class="hero-video" src="/vkclips_20260321070819.mp4" muted playsinline preload="metadata"></video>
</div>
```

### Логика смены видео (inline `<script>`)

```
- Массив из 3 video элементов
- currentIndex = 0
- Десктоп: setInterval(10000) для crossfade — текущее opacity 0, следующее opacity 1, transition 1s
- Мобилка: слушаем событие `ended` на каждом видео → переключаем на следующее
- При переключении: следующее видео .play(), текущее .pause() + currentTime = 0
- Story progress bar (мобилка): CSS animation width от 0% до 100% за duration видео, обновляется через timeupdate
```

### Story Progress Bar (только мобилка)

```html
<div class="story-progress"> <!-- hidden на десктопе -->
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
- Контейнер: `flex gap-1 px-4 pt-4` абсолютно позиционирован сверху
- Каждый bar: `h-[2px] flex-1 rounded-full bg-white/20`
- Fill: `h-full rounded-full bg-brand-orange`, ширина обновляется через JS (currentTime / duration * 100%)
- Пройденные бары: fill = 100%, будущие = 0%

### CSS

```css
.hero-video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 120%; /* для параллакса */
  object-fit: cover;
  opacity: 0;
  transition: opacity 1s ease;
}

.hero-video.active {
  opacity: 1;
}
```

### Оптимизация производительности

- `preload="metadata"` на неактивных видео — не грузим все 3 сразу
- При приближении к переключению (за 2с) ставим `preload="auto"` на следующее видео
- `will-change: opacity` только во время transition, убираем после
- Fallback: если видео не загрузилось — webp-картинка `hero-background.webp` (уже есть)
- Параллакс через `transform: translateY()` (GPU-ускорение, без layout thrashing)

### Файлы видео

Видео остаются в `public/` (уже там). Переименовывать не нужно — используем текущие имена. Старый `public/video/hero-video.mp4` и `src/assets/video/hero-video.mp4` можно удалить после замены.

## Что НЕ меняется

- Весь текстовый контент hero (заголовок, описание, CTA)
- Статистика внизу (600+ клиентов, 5+ лет, 4 дня/неделю)
- Scroll indicator с bounce-анимацией
- Навигационные ссылки
- Film grain overlay
- Градиентные оверлеи (адаптируем направление, но принцип тот же)

## Затрагиваемые файлы

1. `src/lib/components/HeroSection.astro` — основные изменения (HTML + CSS + JS)
2. Удаление: `public/video/hero-video.mp4`, `src/assets/video/hero-video.mp4`
