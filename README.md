# Kiselgram

Self-hosted messaging platform — personal chats, groups, channels, stories, polls, and WebRTC video calls. Java backend (Javalin + Hibernate) with a JSON API and a pure-JS SPA frontend.

[![CI](https://github.com/kiselgram/kiselgram/actions/workflows/ci.yml/badge.svg)](https://github.com/kiselgram/kiselgram/actions/workflows/ci.yml)
[![CD](https://github.com/kiselgram/kiselgram/actions/workflows/cd.yml/badge.svg)](https://github.com/kiselgram/kiselgram/actions/workflows/cd.yml)

## Build

Requires JDK 21.

```bash
./gradlew build          # compile + run tests
./gradlew installDist    # app distribution under build/install/KiselgramJava
./gradlew run            # run locally
```

## Docker

```bash
docker build --platform linux/amd64 -t kiselgram-app:latest .
```

CI builds the image on every push; CD builds and pushes to GHCR on release, and can deploy on an explicit `workflow_dispatch` with `deploy: true`.

## Testing

```bash
./gradlew test
```

JUnit 5 + Mockito. Test source in `src/test/java/`.

## Architecture

**Backend:** Java 21 / Javalin 6 / Hibernate 6 / PostgreSQL. Config in `config/kis.toml`.

**Routes:** Javalin route classes under `src/main/java/ru/kiselgram/web/route/` (auth, chat, groups, channels, stories, calls, premium, push, admin, ...).

**Models:** JPA entities under `src/main/java/ru/kiselgram/web/model/` mirroring the Kiselgram domain (Message, Chat, Story, Call, VideoCall, Poll, User, ...).

**Auth:** Bearer token (`UserSession.session_token`).

**Message encryption:** AES-256-GCM at rest.

**Frontend:** Monolithic HTML shell (`src/main/resources/public/`) with JS modules extending `window.K`. Pure `fetch()`-based SPA.

## Domain structure

```
kiselgram.ru              ─ Landing page
web.kiselgram.ru          ─ SPA web app
api.kiselgram.ru          ─ API backend
admin.kiselgram.ru        ─ Admin panel
cdn.kiselgram.ru          ─ Uploaded files
desktop.kiselgram.ru      ─ Desktop downloads
docs.kiselgram.ru         ─ Documentation
help.kiselgram.ru         ─ Help center
call.kiselgram.ru         ─ Video call rooms
```

## License

Proprietary. See `LICENSE`.