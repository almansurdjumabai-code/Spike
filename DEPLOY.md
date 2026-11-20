# SpikeClip: как устроен и как деплоится

SpikeClip продаётся как **десктоп-приложение для Windows и Mac**. Поиск пиков чата (клип: 20 с до пика и 10 с после) и нарезка вертикальных клипов 9:16 идут **на компьютере пользователя**. На сервере нет ни видео, ни очередей рендера, ни хранилища клипов.

| Папка | Что это | Где работает |
|---|---|---|
| [`backend/`](backend/) | Лёгкий веб-API: аккаунты, оплата Paddle, лицензионные ключи `CLIP-XXXX-XXXX-XXXX`, их активация и проверка. Описание эндпоинтов и схема базы — в [`backend/README.md`](backend/README.md) | Сервер (Render, Docker) |
| [`frontend/`](frontend/) | Сайт: лендинг, тарифы, личный кабинет `/app` (ключ, загрузка приложения), админка `/admin`, юридические страницы | Vercel |

Само десктоп-приложение делается отдельно и подключается к этому API по контракту из [`backend/README.md`](backend/README.md#desktop-app-contract). Прежний движок нарезки удалён из репозитория (он остался в истории git).

```
Браузер ──HTTPS──▶ сайт (Vercel) ──HTTPS──▶ backend/ (Render) ──▶ Postgres (ключи, аккаунты)
                                               ▲
Paddle ──webhook (подписан)────────────────────┘
Десктоп-приложение ──/v1/license/activate|validate──▶ backend/
       └─ локально на ПК: пики чата → клипы 9:16
```

---

## 1. API (`backend/`)

Render: сервис с **Root Directory = `backend`** (Dockerfile подхватится сам), бесплатного или Starter-плана хватает. Готовый Blueprint — [`render.yaml`](render.yaml).

| Переменная | Нужна | Назначение |
|---|---|---|
| `DATABASE_URL` | **да** | Postgres (например бесплатный Neon: `postgresql://…?sslmode=require`). Без него ключи пишутся в SQLite-файл, который бесплатный хост **стирает при каждом перезапуске** |
| `ADMIN_TOKEN` | да | токен владельца для `/admin/*` (выдать/отозвать ключ вручную). Старое имя `SPIKECLIP_API_TOKEN` тоже работает |
| `CORS_ORIGINS` | да | адрес сайта, например `https://spikeclip-app.vercel.app` (старое `SPIKECLIP_CORS_ORIGINS` тоже работает) |
| `PADDLE_WEBHOOK_SECRET` | да | Paddle → Events → Notifications → destination → Secret key |
| `SIGNUP` | нет | `open` (по умолчанию), `invite` (+ `INVITE_CODE`) или `closed` |
| `DOWNLOAD_WINDOWS_URL`, `DOWNLOAD_MAC_URL`, `APP_VERSION` | когда будут сборки | где лежат установщики. Ссылку получает **только владелец активного ключа** (`GET /downloads/{windows,mac}`); публично видно лишь, какие сборки есть |

Ключ клиента Paddle и ID цен уже вшиты в `backend/app/paddle.py` (переменные `PADDLE_*` их переопределяют).

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

1. Соберите установщик (Windows `.exe`, macOS `.dmg`).
2. Загрузите его туда, где ссылку никто не угадает (например приватный бакет Cloudflare R2 или S3 со случайным именем файла), и впишите ссылку в `DOWNLOAD_WINDOWS_URL` / `DOWNLOAD_MAC_URL` на Render. Сайт покажет кнопку скачивания только подписчикам.
3. В приложении: при первом запуске — экран ввода ключа → `POST /v1/license/activate`; при каждом запуске раз в несколько дней — `validate`. Ключ Pro работает на **1 компьютере**, Max — на 3; перенести ключ на новый ПК можно в кабинете («Release»). Даже если установщик утечёт, без купленного ключа он не запустится.

---

## 4. Оплата через Paddle

Paddle — продавец (Merchant of Record): проводит оплату, берёт налоги США и НДС ЕС, делает возвраты и через подписанный webhook сообщает API о подписках. Webhook **выпускает лицензионный ключ** при первой оплате и обновляет его срок, тариф и статус при продлении, смене тарифа и отмене (`backend/app/paddle.py`).

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
