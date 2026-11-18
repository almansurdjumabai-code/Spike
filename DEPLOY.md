# SpikeClip: деплой в облако

Репозиторий состоит из двух независимо деплоящихся частей:

| Папка | Что это | Как деплоится |
|---|---|---|
| [`backend/`](backend/) | Python-движок: загрузка видео (yt-dlp), транскрипция (faster-whisper), поиск моментов (LLM + аудио/видео-сигналы), **нарезка и рендер клипов (FFmpeg)**, публикация. HTTP API + WebSocket на FastAPI. | Docker-образ (`backend/Dockerfile`) на любом хостинге контейнеров |
| [`frontend/`](frontend/) | React + TypeScript + Tailwind интерфейс. Собирается как статический сайт (`npm run build:web`) **или** как десктоп-приложение Windows (Electron, `npm run package`). | Vercel / Netlify / Cloudflare Pages / nginx-контейнер |

Остальные папки в корне (`site/`, `web/`, `whop-app/`, `feedback-relay/`, `twitch-proxy/`, `docs/`) — отдельные проекты (лендинг, браузерная демо-версия, воркеры Cloudflare, документация) и к этим двум частям не относятся.

```
Браузер ──HTTPS──▶ frontend (статика)
   │
   └──HTTPS / WSS + токен──▶ backend (FastAPI :8765) ──▶ FFmpeg, Whisper, LLM (Ollama или OpenRouter)
                                   │
                                   └──▶ /data (постоянный диск: видео, клипы, SQLite)
```

---

## 1. Backend

### Переменные окружения

Полный список — в [`backend/.env.example`](backend/.env.example).

| Переменная | Обязательна | Назначение |
|---|---|---|
| `SPIKECLIP_API_TOKEN` | **да** | Общий секрет. Без него сервер **откажется** слушать публичный интерфейс. Сгенерировать: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `SPIKECLIP_CORS_ORIGINS` | да | Адрес фронтенда, например `https://app.example.com` (через запятую, если их несколько) |
| `SPIKECLIP_ALLOWED_HOSTS` | да | Домен самого API, например `api.example.com` (`*` — любой; не рекомендуется) |
| `SPIKECLIP_DATA_DIR` | нет | По умолчанию `/data` — сюда нужно смонтировать постоянный диск |
| `PORT` | нет | Большинство платформ задают его сами; иначе 8765 |
| `SPIKECLIP_OLLAMA_HOST` | нет | Адрес Ollama, если LLM запускается рядом; иначе выберите облачного провайдера (OpenRouter) в Settings → AI |

Токен принимается как `Authorization: Bearer …`, заголовок `X-SpikeClip-Token` или параметр `?access_token=…` (последний нужен для `<video>`, `<img>` и WebSocket, которые не умеют слать заголовки). Без токена открыты только `/health` и OAuth-колбэки (`…/callback…`).

### Сборка и запуск

```bash
docker build -t spikeclip-backend --build-arg SPIKECLIP_VERSION=2.1.0 backend/
docker run -p 8765:8765 -v spikeclip-data:/data --env-file backend/.env spikeclip-backend
```

### Render (готовый Blueprint)

В корне лежит [`render.yaml`](render.yaml): веб-сервис из `backend/Dockerfile` и **постоянный диск 50 ГБ в `/data`** (видео, клипы, SQLite-база и кэш моделей). Токен Render генерирует сам. CORS уже настроен на `spikeclip-app.vercel.app`, а домен `*.onrender.com` бэкенд разрешает автоматически.

1. Откройте https://dashboard.render.com/blueprint/new?repo=https://github.com/almansurdjumabai-code/Spike, дайте Render доступ к репозиторию, проверьте цену и нажмите **Apply**.
2. Когда сервис поднимется, скопируйте его адрес (`https://spikeclip-backend-….onrender.com`) и значение `SPIKECLIP_API_TOKEN` (Environment).
3. В Vercel задайте `VITE_API_BASE=<адрес>` и сделайте Redeploy фронтенда.
4. Откройте сайт и введите токен. Затем в Settings → AI выберите облачного провайдера (OpenRouter): Ollama на Render не запускается.

Диск у Render доступен только на платных тарифах. Он привязывает сервис к одному экземпляру, а при деплое сервис ненадолго перезапускается — для этой архитектуры это нормально.

### Другие платформы

На Railway / Fly.io / Google Cloud Run укажите `backend/` как корень сборки (Dockerfile подхватится сам), задайте переменные выше и подключите постоянный диск в `/data`. Образ публикуется и в GHCR воркфлоу `.github/workflows/docker-image.yml` (при пуше тега).

### Ресурсы

Обработка видео тяжёлая. Ориентиры из исходного проекта: **12 ГБ RAM и 4 vCPU** — минимум, при котором рендер вообще проходит (8 ГБ анализирует видео, но клипов не выдаёт); примерно час исходника на 12 ГБ. Образ собран на CPU-версии PyTorch. Для GPU нужен образ на базе `nvidia/cuda` и CUDA-сборка `torch` — см. [`docs/DOCKER.md`](docs/DOCKER.md).

Воркер обрабатывает **одно видео за раз** и хранит очередь в SQLite на диске. Поэтому backend нужно запускать **одним экземпляром** (не масштабировать горизонтально) с постоянным диском.

---

## 2. Frontend

Адрес бэкенда встраивается в сборку (это статический сайт). Задайте его в [`frontend/.env.example`](frontend/.env.example) → `.env.production` или в панели хостинга:

```
VITE_API_BASE=https://api.example.com
```

**Vercel:** Root Directory = `frontend` (`frontend/vercel.json` уже настроен).
**Netlify / Cloudflare Pages:** base `frontend`, build `npm run build:web`, publish `dist-web`, переменная `ELECTRON_SKIP_BINARY_DOWNLOAD=1`.
**Свой сервер:**

```bash
docker build -t spikeclip-frontend --build-arg VITE_API_BASE=https://api.example.com frontend/
docker run -p 8080:8080 spikeclip-frontend
```

При первом открытии сайт спросит токен доступа (`SPIKECLIP_API_TOKEN`) и сохранит его в браузере. В Electron-версии экрана с токеном нет: десктоп по-прежнему работает с локальным движком на `127.0.0.1:8765`.

---

## 3. Локальная разработка

```bash
docker compose up --build        # backend на :8765 + интерфейс на :5173 + Ollama
```

или без Docker: `pip install -r backend/requirements.txt`, затем `cd frontend && npm install && npm run dev:web` (в браузере) или `npm run dev` (Electron сам запустит `backend/main.py`).

---

## 4. Ограничения веб-версии

Эти возможности рассчитаны на локальный ПК и в облаке работают иначе или не работают:

- **Выбор локального файла** (кнопки «открыть видео/аудио») — это диалоги Electron; в браузере они отключены. Видео добавляются по ссылке (YouTube / Twitch / Kick). Загрузка файлов с компьютера пользователя потребует отдельного эндпоинта.
- **OAuth через localhost.** Вход YouTube для публикации (`publish/oauth.py`) и Discord (`/discord/callback`, «работает только на порту 8765») рассчитаны на loopback-адрес. Для облака нужно зарегистрировать redirect URI на домене API у Google/Discord.
- **Remote rendering** (`remote_render/`, порт 8766) — второй ПК для рендера; в облаке не нужен.
- **Модели и Ollama** в упакованном десктопе идут в комплекте; в облаке нужен отдельный сервис Ollama или облачный провайдер.

---

## 5. Ребрендинг: что сменить вручную

Все упоминания Clips Kitty / Clips Studio в коде, конфигах, документации и именах файлов заменены на SpikeClip, а ссылки на сам репозиторий переведены на `ColinGPT9/spikeclip`. Нетронутыми оставлены ссылки на **чужие внешние ресурсы**, которые под новым именем пока не существуют. Если подменить их вслепую, они либо сломаются, либо поведут на чужой аккаунт:

| Ресурс | Где | Что сделать |
|---|---|---|
| Репозиторий `github.com/ColinGPT9/spikeclip` | ~1000 ссылок, автообновление, бейджи | Переименовать/создать репозиторий; если владелец другой — `git grep -l ColinGPT9/spikeclip \| xargs sed -i 's#ColinGPT9/spikeclip#ВЛАДЕЛЕЦ/spikeclip#g'` |
| GitHub Pages `colingpt9.github.io/spikeclip` | сайт, sitemap | Появится после переименования репозитория (Pages не делают редирект со старого адреса) |
| `paypal.me/clipsstudio` | кнопки доната, `.github/FUNDING.yml` | Заменить на свой PayPal или убрать |
| `@ClipsKitty2` (YouTube, X, TikTok, Instagram) | README, сайт | Свои соцсети |
| `*.clipsstudio.workers.dev`, `clips-kitty-web.vercel.app` | `config/settings.yaml` (feedback relay), CORS воркеров | Задеплоить `feedback-relay/`, `twitch-proxy/`, `web/` под своим аккаунтом и подставить адреса |
| `ColinGPT9/awesome-clips-kitty`, `clips-kitty-obs-plugin`, GTA 6 plugin | каталог плагинов, интеграции | Форкнуть или оставить. Учтите: в манифестах плагинов ключ совместимости переименован `clipskitty` → `spikeclip`, так что плагины из старого каталога нужно обновить |
| `woopsocial.com/?via=clipskitty` | реферальная ссылка | Свой реферальный код или обычная ссылка |
| Microsoft Store (`9NB6XT7DSQZZ`, identity `SpikeClip.SpikeClip`, publisher) | `frontend/electron-builder.yml`, `docs/MSSTORE.md` | Зарезервировать своё имя в Partner Center и вписать выданные identity/publisher |
| Картинки с логотипом (маскот, скриншоты, GIF) | `docs/brand`, `docs/store-screenshots`, `site/assets` | Бинарные файлы: на изображениях осталось старое название, их нужно перерисовать |

Также: папка данных десктопа теперь `%LOCALAPPDATA%\SpikeClip` (была `Clips Studio`). У существующих пользователей старой программы библиотека автоматически не перенесётся.
