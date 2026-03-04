# 📋 task_plan.md — Project Task Plan

> **Living document.** Updated continuously as phases complete.

---

## 🎯 Project Overview

- **Project Name:** AI Pulse Dashboard
- **North Star:** A gorgeous, interactive dashboard aggregating the latest AI news from top newsletters, with 24-hour refresh and article bookmarking.
- **Initialized:** 2026-03-03

---

## 🟢 Protocol 0: Initialization

- [x] Create `task_plan.md`
- [x] Create `findings.md`
- [x] Create `progress.md`
- [x] Initialize `gemini.md` (Project Constitution)
- [x] Ask Discovery Questions
- [x] Define Data Schema in `gemini.md`
- [x] Get Blueprint approved → ⏳ awaiting user review

---

## 🏗️ Phase 1: B - Blueprint

- [x] Discovery Questions answered
- [x] North Star defined
- [x] Integrations identified (Ben's Bites + The Rundown AI RSS)
- [x] Source of Truth defined (RSS feeds → browser localStorage)
- [x] Delivery Payload defined (dashboard with 24h refresh)
- [x] Behavioral Rules defined
- [x] JSON Input/Output Schema written in `gemini.md`
- [/] Blueprint approved by user → ⏳ awaiting

---

## ⚡ Phase 2: L - Link

- [ ] Test RSS feeds via Python script
- [ ] Build `tools/fetch_feeds.py`
- [ ] Write `architecture/scraper-sop.md`
- [ ] Verify JSON output matches schema

---

## ⚙️ Phase 3: A - Architect

- [ ] Scaffold Vite dashboard in `dashboard/`
- [ ] Build design system (`index.css`)
- [ ] Build article card component
- [ ] Build source filter / navigation
- [ ] Build save/bookmark system (localStorage)
- [ ] Integrate feed data into dashboard
- [ ] Wire up 24-hour refresh logic

---

## ✨ Phase 4: S - Stylize

- [ ] Dark-mode glassmorphism theme
- [ ] Micro-animations & hover effects
- [ ] Responsive layout
- [ ] User feedback loop

---

## 🛰️ Phase 5: T - Trigger

- [ ] Supabase integration (future)
- [ ] Cron-based auto-refresh (future)
- [ ] Cloud deployment (future)
