---
template: kawaii-storybook
title: "Pawmail"
subtitle: "A friendly inbox for pet parents"
version: "v1.0"
---

<!-- _class: cover -->

###### A PANGAEA DIGITAL LABS STORY

# Meet *Pawmail* 🐾

A warm, friendly email app made just for pet owners — vet reminders, adoption updates, and treat coupons, all in one cozy inbox.

![Pawmail storybook backdrop](/Users/harry/projects/claude-plugins/plugins/docsmith/skills/make-pdf-workspace/iteration-1/eval-0-kawaii-feature-deck/old_skill/outputs/storybook-backdrop.svg)

---

<!-- _class: figure -->

###### SAY HELLO

# Posty, your *mail pup*

![Posty the Pawmail mascot hugging an envelope](/Users/harry/projects/claude-plugins/plugins/docsmith/skills/make-pdf-workspace/iteration-1/eval-0-kawaii-feature-deck/old_skill/outputs/posty-mascot.svg)

Posty fetches every message, wags at good news, and never loses a letter.

---

<!-- _class: cards -->

###### WHAT'S INSIDE

# A *cozy* inbox for every pet 🐶

- **Vet Reminders** Gentle nudges for shots, check-ups, and refills so nothing slips by.
- **Adoption Updates** Follow your shelter's newest friends with photo-first stories.
- **Treat Coupons** Sniff out deals from pet shops, auto-sorted into a happy folder.
- **Paw Profiles** One tidy card per pet — weight, meds, and birthday in a tap.

---

<!-- _class: cards -->

###### HELPFUL TIPS

# Get the most out of *Pawmail* 🦴

- **Tip · Pin a Pet** Pin a Paw Profile to the top so its reminders always greet you first.
- **Tip · Treat Folder** Star a coupon and Posty tucks it into your *Treats* folder for later.

> 🐾 Little habits, happy pets — a pinned profile and a starred treat keep the whole pack on track.

---

<!-- _class: path caution -->

###### READ BEFORE SENDING

# A gentle *heads-up* 🦊

![Posty the Pawmail mascot](/Users/harry/projects/claude-plugins/plugins/docsmith/skills/make-pdf-workspace/iteration-1/eval-0-kawaii-feature-deck/old_skill/outputs/posty-mascot.svg)

- **Attachments** Photos over 25 MB won't send — shrink that adorable album first.
- **Reply-All** Double-check before barking to the whole litter; some replies are just for the vet.

> Caution — once Posty delivers a letter, it can't be un-fetched. Peek before you send!

---

<!-- _class: split -->

###### FOR THE BUILDERS

# Send a letter in *one call* 🦉

The Pawmail Send API takes a tiny JSON body and hands it to Posty.

```js
await pawmail.send({
  to:      "vet@happytails.pet",
  from:    "me@pawmail.app",
  subject: "Bella's checkup 🐶",
  body:    "See you Tuesday at 3!"
});
// → { id: "msg_7a3f", status: "queued" }
```

---

<!-- _class: closing -->

###### THE END (FOR NOW)

# Happy mail, *happy pets* 🐾

Pawmail keeps every pet parent close to the ones they love. Fetch a treat, send a hug — Posty's got the rest.
