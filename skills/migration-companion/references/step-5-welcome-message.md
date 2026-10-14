# Step 5 — Welcome message (render verbatim)

> **When to read:** When Step 4 is complete. Contains the exact welcome message to display to the user. This file is part of the [migration-companion skill](../SKILL.md); `<SKILL_DIR>` refers to that skill's install directory.

The migration is complete. Display the following message to the user — render it exactly as shown, preserving the section headings, icons, and line breaks:

---

![Contentstack](https://images.contentstack.io/v3/assets/blt77d44a06c81b1730/blt2e24a315fedaeaf7/68bc10f25f14881bc908b6c2/CS_OnlyLogo.webp)

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   🚀  Welcome to Contentstack!                                   ║
║                                                                  ║
║   The Agentic Experience Platform                                ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

> *"The world's best digital experiences run on Contentstack."*

**🎊 Your migration is complete.**

Your content, content types, assets, and website code have all successfully moved from Contentful to Contentstack. Here's a quick recap of what just happened:

| ✅ | What was migrated |
|---|---|
| 📦 | Content types & field definitions |
| 🖼️ | Assets & media |
| 📝 | Entries & localized content |
| 💻 | Website data-layer code |

### 📂 Where to find your migrated files

Using the exact paths captured during this session, fill in and display this table:

| Artifact | Location |
|---|---|
| 🗂️ **Contentful export** | `<EXPORT_JSON>` (from Step 3) |
| 📦 **Contentstack import bundle** | `<BUNDLE_DIR>` (from Step 3) |
| 🔑 **Stack credentials** | `<METADATA_PATH>` (from Step 3) |
| 📋 **Import logs** | `<LOG_DIR>` (from Step 3) |
| 💻 **Migrated website code** | The `repoPath` the user provided in Step 4 |
| 🔍 **Code migration log** | `session.log` in the directory printed by `log.sh <target> path` (Step 4) |

Do not use default or guessed paths — substitute only the real paths you captured from each step's command output.

---

### 🌟 You're now on the platform trusted by the world's top brands

Contentstack powers digital experiences for enterprises across retail, media, finance, and beyond — delivering content at scale, across every channel, without compromise.

Here's what you've unlocked:

| Capability | What it means for you |
|---|---|
| ⚡ **Composable architecture** | Mix and match best-of-breed tools — your stack, your way |
| 🌍 **Multi-region delivery** | Content served fast, anywhere on the globe |
| 🔄 **Omnichannel publishing** | Web, mobile, IoT, voice — one content hub for all |
| 🛡️ **Enterprise-grade security** | Security and compliance details at the [Contentstack Trust Center](https://www.contentstack.com/trust) |
| 🤝 **Dedicated support** | Real humans, not just docs — onboarding, migrations, and beyond |
| 🧩 **Marketplace & integrations** | Pre-built apps and connectors — plug in what you already use |

---

### 🚦 Recommended next steps

1. **Verify your live site** — start your app with the new `CS_*` env vars and confirm pages render against Contentstack.
2. **Explore the Contentstack dashboard** — invite your team, set up roles, and configure publishing workflows.
3. **Set up webhooks & automation** — trigger deploys, Slack alerts, or custom workflows on publish events.
4. **Review the Contentstack Docs** — [contentstack.com/docs](https://www.contentstack.com/docs) is your go-to for Delivery SDK, GraphQL, and Live Preview guides.
5. **Talk to your account team** — let them know you're live; they can unlock additional features and walk you through advanced capabilities.

---

> 💡 **Tip:** Bookmark the [Contentstack Developer Hub](https://developers.contentstack.com) — it has SDK references, starter apps, and video tutorials to help you get the most out of your new platform.

---

*Congratulations on completing your migration.  
You've made the right call — the world's best digital experiences are built on Contentstack, and now yours will be too.* 🚀
