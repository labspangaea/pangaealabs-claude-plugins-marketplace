---
template: kawaii-storybook
title: "Cloud Safety, Explained"
subtitle: "A gentle storybook tour of keeping things safe in the cloud"
date: auto
version: "v1.0"
---

<!-- _class: cover -->

###### A NIMBUS STUDIO STORYBOOK

# Cloud *Safety*, Explained

A gentle tour of how three little friends — 🐻 🦊 🦉 — keep their things safe up in the clouds.

---

<!-- _class: bigstat -->

###### WHY IT MATTERS

# 9 *in 10*

Most mishaps in the cloud are not clever break-ins — they start with a small, *human* slip: a shared link left open, a forgotten password, a door nobody locked.

---

<!-- _class: pillars -->

###### THE THREE PILLARS

# The shape of a *safe* cloud

- **Confidentiality** Only the right friends can peek inside. 🐻 keeps the honey jar lidded.
- **Integrity** Nothing changes without you knowing. 🦊 notices if even one acorn moves.
- **Availability** Your things are there when you reach for them. 🦉 keeps the lights on at night.

---

<!-- _class: path accept -->

###### A SAFE HABIT

# Two keys are better than *one* 🐻

![A pastel cloud village guarded by a friendly lock](/Users/harry/projects/pangaealabs-claude-plugins-marketplace/plugins/docsmith/examples/kawaii-storybook/diagrams/hero.svg)

- **Concept** Add a second little check after your password — a code from your phone.
- **Appeal** Even if someone learns your password, they still can't get in.
- **Reality** It takes five seconds and stops almost every sneaky login.

> **Verdict** — Turn it on everywhere. This is the single kindest thing you can do for yourself. 🐻

---

<!-- _class: path reject -->

###### A RISKY SHORTCUT

# "I'll just reuse this *password*" 🦊

- **Concept** One easy password, used on every single door, so it's simple to remember.
- **Appeal** Nothing new to memorise — log in fast, move on with your day.
- **Reality** One leak anywhere, and every door you own swings open at once.

> **Verdict** — Don't. Give each door its own key, and let a password manager carry the ring. 🦊

---

<!-- _class: path caution -->

###### HANDLE WITH CARE

# Sharing a *link* with the world 🦉

- **Concept** "Anyone with the link can view" — one tap, and your file is shareable.
- **Appeal** No accounts, no fuss; perfect for a quick hand-off to a friend.
- **Reality** Links wander. Forwarded, indexed, screenshotted — they outlive the moment.

> **Verdict** — Fine for the harmless stuff. Pause and set an expiry before sharing anything tender. 🦉

---

<!-- _class: laws -->

###### FOUR GENTLE LAWS

# Rules the village *lives* by

- **Least privilege** Give each friend only the keys they truly need — no more.
- **Trust, but verify** A friendly face is lovely; a quick check is wiser. 🦊
- **Patch early** Tiny cracks let weather in. Fix the little ones before they grow.
- **Back it up** A second copy, kept apart, turns a bad day into a small one. 🦉

---

<!-- _class: scorecard -->

###### A QUICK SELF-CHECK

# How *cloud-ready* are you?

| Good habit | Doing it? | Why it helps |
| :--- | :---: | :--- |
| Unique passwords everywhere | 🟢 | One leak can't unlock the rest |
| Two-step login switched on | 🟢 | A second key stops sneaky logins |
| Old share links cleaned up | 🟡 | Wandering links quietly add up |
| Regular backups, kept apart | 🔴 | Without it, one bad day is forever |

> **Conclusion** — Two greens is a fine start. Tend the amber and the red this week, and the village sleeps easy. 🐻

---

<!-- _class: flow -->

###### WHAT TO DO IF SOMETHING FEELS OFF

# Five calm *steps* 🦊

- **Pause** Don't panic and don't delete. Take a breath.
- **Disconnect** Step the device off the network so nothing spreads.
- **Change keys** Reset the password and revoke active sessions.
- **Tell someone** A trusted friend or helper makes it lighter.
- **Learn** Note what slipped, so the door stays shut next time.

---

<!-- _class: scenarios -->

###### A DAY IN THE VILLAGE

# When habits *meet* the real world

- **Strange email** → **Hover, don't click** → **Phishing dodged** 🦉
- **New app wants access** → **Grant the least it needs** → **Nothing over-shared** 🐻
- **Laptop left at the café** → **Remote-lock from your phone** → **Calm, not chaos** 🦊

---

<!-- _class: roadmap -->

###### YOUR FIRST WEEK

# A friendly *starter* path

- **Day 1** Turn on two-step login for your email — the master key to everything.
- **Day 2** Install a password manager and let it invent strong, unique keys.
- **Day 4** Walk through old shared links and retire the ones you've forgotten.
- **Day 7** Set up one automatic backup, kept somewhere separate. Then rest. 🦉

---

<!-- _class: figure bare -->

###### THE WHOLE PICTURE

# One safe little *village*

![A pastel cloud village guarded by a friendly lock, with perches for the bear, fox, and owl](/Users/harry/projects/pangaealabs-claude-plugins-marketplace/plugins/docsmith/examples/kawaii-storybook/diagrams/hero.svg)

Strong keys, careful sharing, and a spare copy — that's the whole story.

---

<!-- _class: split -->

###### A TINY EXAMPLE

# Lock the *door* in one line

A backup is just a habit a computer can keep for you. Here's the friendly version 🦊 — schedule a copy, somewhere apart, every night while you sleep.

```bash
# Copy today's files to a safe, separate home — every night at 2am
rclone sync ~/Documents remote:nightly-backup \
  --backup-dir remote:attic/$(date +%F) \
  --log-level INFO
```

---

<!-- _class: pillars -->

###### TWO NOTES FROM THE VILLAGE

# Carry *these* with you 🦉

<aside class="callout tip">

**Pro tip** — A password manager is a friend, not a chore. Let it remember the keys so your brain can hold the *one* that unlocks it.

</aside>

<aside class="callout warning">

**Watch out** — "Anyone with the link" really does mean *anyone*. Before you share, ask: would I mind a stranger finding this? If yes, set an expiry.

</aside>

---

<!-- _class: quote -->

###### A LITTLE WISDOM

> Safety in the cloud isn't a *fortress* — it's a handful of small, kind habits, kept every day.

---

<!-- _class: statement -->

###### REMEMBER

# You don't need to be *perfect*. 🐻

You just need to be a little *careful*, a little *consistent*, and kind to your future self.

---

<!-- _class: closing -->

###### THE END

# Stay *cosy*, stay safe ☁️

Unique keys, careful sharing, a spare copy. That's all it takes. 🐻 🦊 🦉

---

*A Nimbus Studio storybook · made with docsmith*
