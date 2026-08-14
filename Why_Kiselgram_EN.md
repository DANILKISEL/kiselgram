# Why Kiselgram?

*A short, honest walkthrough for the skeptical.* You've seen a hundred new "messengers" come and go — most are clones, vaporware, or just a Python demo wrapped in a nice logo. Fair. So before you sign up, here is exactly what Kiselgram is, what it does, and how it's built — no marketing fluff, no fake numbers.

---

## 1. It actually exists and actually works

Kiselgram is a live, running messaging platform — not a Figma mockup. The production build is a Flask + Python 3.10 backend with a vanilla JavaScript SPA, deployed on a real server. You can log in today, send messages, create a group or a channel, and watch a friend reply in real time. There is nothing to "wait for later."

**Core, shipped today:**
- Real-time 1-on-1 chat with typing indicators and read receipts
- Groups with roles, admins, invites, and member management
- Broadcast channels with unlimited subscribers
- Stories (photos/videos that expire in 24h)
- File sharing: images, videos, audio, documents — with in-app previews
- Polls, pinned messages, replies, forwards, scheduled messages
- Global search across users, groups, and channels
- Message editing, deletion (incl. "delete for all"), read receipts
- Themes, fonts, chat customization
- Push notifications (Web Push / VAPID)

## 2. Security and privacy

This is the part where everyone gets skeptical, and rightly so — "security" is the most overused word in software. So instead of promising, here's what exists as concrete, working features:

- **Everything is designed to be hard to take from you.** Your password is stored hashed, never in plain text. Logging in can require a one-time code to your email, so a password alone isn't enough. You can view every active session on your account and terminate any of them remotely with one click. There is 2FA-aware handling, OTP login, and full verification flows — not as promises, as buttons.
- **There is nothing on Kiselgram worth stealing.** No stored card numbers, no passport scans, no bank connections. Worst case for anyone "hacking" an account, they'd read casual chat about dinner plans. A stolen Kiselgram account is a lot of effort for essentially no prize — the practical value is close to zero, which is the point: the honest way to protect your users is to have as little to steal as possible.
- **You are in control of your own inbox.** Block, mute, archive, control visibility, report. Blocked users stay blocked; muted chats stay muted; deleted message stay deleted (including "delete for all").
- **Reports go somewhere.** There's a real moderation pipeline behind the report button — submissions are reviewed and acted on by an admin, not swallowed into a void.
- **It's boring, ordinary technology.** Flask + SQLAlchemy + a standard web frontend. Boring is a feature: no exotic closed-source layers, no mystery black box, nothing "special" that could silently break. It's the same kind of stack as a thousand other reliable applications, and it's inspectable by anyone who knows how to run a server.

And the uncomfortable truth every app should tell you: **no messenger is 100% unbreakable — not even the giants.** Anyone who promises that is lying to you. What Kiselgram offers is the honest, industry-standard baseline: hashed credentials, verified sign-in, session control, user-in-control privacy settings, and real moderation. Then it lets you test it yourself.

## 3. The "skeptic" checklist

| "Yeah, but…" | Reality |
|---|---|
| "It's probably just a template" | Custom Flask backend, custom SPA, custom API (`/api.v2`), 25+ feature modules. |
| "No one will maintain it" | Active development — v4.0 shipped with stories, premium fonts, chat customization, global search. |
| "Security is a joke" | Hashed credentials, email/OTP verification, session management, block/mute/report, real moderation review. |
| "It's a dead demo" | It runs in production today; you can verify by using it. |
| "I'll get locked in / spammed" | Block, mute, archive, privacy settings, "delete for all", and real moderation. |
| "Stories & extras are gimmicks" | Polls, scheduled messages, read receipts, global search, forwarded & reply context — everyday tools. |

## 4. Where it's going (Premium)

Kiselgram Premium unlocks polish on top of the free core: 11 premium fonts, story reactions/views analytics, custom wallpapers, and priority support. The full messenger is free; Premium is optional and cosmetic-forward.

## 5. What's under the hood (open to inspection)

```
Backend:  Flask, SQLAlchemy, SQLite → Postgres-ready config
Frontend: Vanilla ES6+ (no heavy framework lock-in), CSS3, HTML5
Realtime: Typing/presence + message polling
Deploy:   Production WSGI server, Docker-ready (docker-compose included)
API:      Versioned API endpoints (api.v2 / api.v3) — clean contract
```

Nothing is obfuscated, no third-party analytics phone-home, no opaque SDKs. If you can run a server, you can run Kiselgram yourself and verify every claim in this document.

---

## The honest bottom line

Kiselgram doesn't promise to replace anything — it offers a complete, working, privacy-respecting messenger *right now*, built with boring, auditable technology. The fastest way to test these claims is to use it: send a message, start a group, create a channel, check a read receipt, try terminating a session. The features are real because you can touch them.

**Try it once. Skepticism welcome — that's exactly how we want to be judged.**

© 2026 Kiselgram