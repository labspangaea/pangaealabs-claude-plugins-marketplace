---
template: kawaii-storybook
title: "Pawmail"
subtitle: "A friendly email app for pet owners"
date: auto
version: "v1.0"
---

<!-- _class: cover -->

![bg cover](/Users/harry/projects/claude-plugins/plugins/docsmith/skills/make-pdf-workspace/iteration-1/eval-0-kawaii-feature-deck/with_skill/outputs/scene.svg)

###### PANGAEA DIGITAL LABS

# Meet *Pawmail* 🐾

Inbox, *but make it cuddly* — email built for pet owners and the humans who love them.

---

<!-- _class: figure bare -->

###### SAY HELLO

# This is *Postie* the pup 🐶

![Postie the Pawmail mascot, a puppy mail-carrier holding a heart-stamped envelope](/Users/harry/projects/claude-plugins/plugins/docsmith/skills/make-pdf-workspace/iteration-1/eval-0-kawaii-feature-deck/with_skill/outputs/mascot.svg)

Postie fetches every vet reminder, adoption update, and treat-shop coupon — then trots it straight to your inbox.

---

<!-- _class: cards3 -->

###### WHY PET OWNERS LOVE IT

# A *warmer* inbox 🐾

- **Vet Reminders** Auto-sorts shot dates and check-ups into a gentle, on-time nudge.
- **Treat Deals** Bundles every pet-shop coupon into one tidy weekly digest.
- **Paw Profiles** One folder per furry friend, so nothing gets lost in the litter.

---

<!-- _class: split -->

###### HELPFUL TIPS

# Get the *most* out of Pawmail 🦴

<aside class="callout tip">

**Tag your pets early.** Add each companion to a Paw Profile on day one — Postie then routes their mail automatically, no rules to fiddle with.

</aside>

<aside class="callout tip">

**Pin the vet.** Star your clinic's address so appointment confirmations always float to the top of the inbox.

</aside>

<aside class="callout warning">

**Watch out for look-alikes.** Coupon emails from unverified shops land in *Sniff-Test* quarantine — open attachments only after Postie marks the sender safe.

</aside>

---

<!-- _class: statement -->

###### FOR DEVELOPERS

# Send mail in *one* call 🐱

Drop a treat in your customers' inbox with the Pawmail Send API — friendly defaults, a heart-warming payload.

```bash
curl -X POST https://api.pawmail.app/v1/send \
  -H "Authorization: Bearer $PAWMAIL_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "human@example.com",
    "from": "postie@pawmail.app",
    "subject": "Bella'\''s vaccine is due 🐾",
    "body": "A gentle nudge from Pawmail!"
  }'
```

---

<!-- _class: closing -->

###### START WITH PANGAEA DIGITAL LABS

# Happy tails, *happy inbox* 🐾🐶

> Pawmail — built with love by Pangaea Digital Labs. Adopt a kinder inbox today.
