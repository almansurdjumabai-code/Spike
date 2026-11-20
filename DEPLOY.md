# SpikeClip: как устроен и как деплоится

SpikeClip продаётся как **десктоп-приложение для Windows и Mac**. Поиск пиков чата (клип: 20 с до пика и 10 с после) и нарезка вертикальных клипов 9:16 идут **на компьютере пользователя**. На сервере нет ни видео, ни очередей рендера, ни хранилища клипов.

| Папка | Что это | Где работает |
|---|---|---|
| [`api/`](api/) | Лёгкий веб-API: аккаунты, оплата Paddle, лицензионные ключи `CLIP-XXXX-XXXX-XXXX`, их активация и проверка. Описание эндпоинтов и схема базы — в [`api/README.md`](api/README.md) | Сервер (Render, Docker) |
| [`frontend/`](frontend/) | Сайт (лендинг, тарифы, личный кабинет `/app` с ключом и загрузками, юридические страницы) **и** оболочка десктоп-приложения (Electron) | Сайт — Vercel; приложение — на ПК пользователя |
| [`backend/`](backend/) | Движок нарезки (скачивание VOD, чат, транскрипция, рендер FFmpeg). Упаковывается **внутрь десктоп-приложения** и запускается локально | ПК пользователя (на сервер больше не деплоится) |

```
Браузер ──HTTPS──▶ сайт (Vercel) ──HTTPS──▶ api/ (Render) ──▶ Postgres (ключи, аккаунты)
                                               ▲
Paddle ──webhook (подписан)────────────────────┘
Десктоп-приложение ──/v1/license/activate|validate──▶ api/
       └─ локально: backend/ (движок) → клипы 9:16 на диске пользователя
```

---

## 1. API (`api/`)

Render: сервис с **Root Directory = `api`** (Dockerfile подхватится сам), бесплатного или Starter-плана хватает. Готовый Blueprint — [`render.yaml`](render.yaml).

| Переменная | Нужна | Назначение |
|---|---|---|
| `DATABASE_URL` | **да** | Postgres (например бесплатный Neon: `postgresql://…?sslmode=require`). Без него ключи пишутся в SQLite-файл, который бесплатный хост **стирает при каждом перезапуске** |
| `ADMIN_TOKEN` | да | токен владельца для `/admin/*` (выдать/отозвать ключ вручную). Старое имя `SPIKECLIP_API_TOKEN` тоже работает |
| `CORS_ORIGINS` | да | адрес сайта, например `https://spikeclip-app.vercel.app` (старое `SPIKECLIP_CORS_ORIGINS` тоже работает) |
| `PADDLE_WEBHOOK_SECRET` | да | Paddle → Events → Notifications → destination → Secret key |
| `SIGNUP` | нет | `open` (по умолчанию), `invite` (+ `INVITE_CODE`) или `closed` |
| `DOWNLOAD_WINDOWS_URL`, `DOWNLOAD_MAC_URL`, `APP_VERSION` | когда будут сборки | ссылки на установщики в личном кабинете (пока пусто — кабинет пишет «Coming soon») |

Ключ клиента Paddle и ID цен уже вшиты в `api/app/paddle.py` (переменные `PADDLE_*` их переопределяют).

Выдать ключ вручную (подарок, тестер, проверяющий Paddle):

```bash
curl -X POST https://<api>/admin/licenses -H "Authorization: Bearer $ADMIN_TOKEN" -H "Content-Type: application/json" -d '{"plan":"pro","email":"friend@example.com","days":30}'
```

---
## 2. Сайт (`frontend/`, Vercel)

Адрес API встраивается в сборку: `VITE_API_BASE=https://<api>` (Vercel → Settings → Environment Variables), затем Redeploy. Root Directory = `frontend`, `frontend/vercel.json` уже настроен.

- `/` — лендинг: оффер, шаги, преимущества, тарифы, FAQ.
- `/app` — личный кабинет: лицензионный ключ (копировать), устройства (отвязать), управление подпиской, загрузки Windows / Mac, инструкция по установке и активации. После оплаты Paddle возвращает сюда.
- `/terms`, `/privacy`, `/refund` — юридические страницы (данные продавца — `LEGAL` в `components/landing/Legal.tsx`).

## 3. Десктоп-приложение

Собирается из `frontend/` (Electron) + `backend/` (движок):

```bash
cd backend && python scripts/build_installer.py      # Windows-установщик → release/
```

Готовый установщик загрузите туда, откуда его можно скачать (GitHub Releases, Cloudflare R2 и т. п.), и пропишите ссылку в `DOWNLOAD_WINDOWS_URL`. Сборки для macOS пока нет. Экран ввода ключа в самом приложении ещё предстоит сделать — контракт API для него описан в [`api/README.md`](api/README.md#desktop-app-contract).

Локальная разработка движка и интерфейса: `docker compose up --build` или `cd frontend && npm run dev` (Electron сам запустит `backend/main.py`).

---

## 4. Оплата через Paddle

Paddle — продавец (Merchant of Record): проводит оплату, берёт налоги США и НДС ЕС, делает возвраты и через подписанный webhook сообщает API о подписках. Webhook **выпускает лицензионный ключ** при первой оплате и обновляет его срок, тариф и статус при продлении, смене тарифа и отмене (`api/app/paddle.py`).

Webhook URL: `https://<api>/billing/paddle/webhook`, события `subscription.*`. Checkout settings → Default payment link: `https://<сайт>/app`.

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
