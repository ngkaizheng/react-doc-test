# Project Wiki

<!--
This file is the permanent source of truth for your project.
Add sections as major decisions are finalized or architecture is established.

Each ## section becomes an entry in index.json, discoverable by the agent.
-->

## Architecture Overview
<!-- Describe the high-level architecture, key patterns, and design philosophy. -->

## Tech Stack
<!-- Languages, frameworks, databases, tools — and why each was chosen. -->

### Vercel
- **Purpose:** Hosting platform for the web application and API routes.
- **Key features used:** Serverless Functions, Edge Functions, and preview deployments.
- **Vercel Cron Jobs:** Scheduled serverless function invocations for recurring tasks (e.g., daily cleanup, periodic syncs). Configured via \ercel.json\ with the \crons\ property.
### Supabase
- **Purpose:** Backend-as-a-Service providing PostgreSQL database, authentication, and real-time subscriptions.
- **Supabase Storage:** Used for file and media asset storage (e.g., user uploads, images, documents). Access controlled via RLS (Row Level Security) policies tied to Supabase Auth.

### Resend
- **Purpose:** Email delivery service for transactional emails (e.g., welcome emails, password resets, notifications).
- **Integration:** Called from Vercel Serverless Functions or Supabase Edge Functions via the Resend SDK.

### BillPlz
- **Purpose:** Payment gateway for invoice generation and payment collection (Malaysia-focused).
- **Integration:** Webhook-based flow — BillPlz sends payment status callbacks to a Vercel API route, which updates order status in Supabase.

### Stripe
- **Purpose:** Primary payment gateway for international credit card transactions.
- **Integration:** Stripe Elements for front-end card collection, Stripe webhooks to Vercel API routes for payment event handling.

## Coding Standards
<!-- Conventions that differ from defaults. Linter rules, naming, file structure. -->

## Key Decisions
<!-- Record of significant decisions and their rationale. Add new entries at the top. -->

### 2026-06-17: Selected Tech Stack (Vercel + Supabase + Resend + BillPlz)
**Context:** Needed to choose a modern, scalable stack for a full-stack web application with scheduled jobs, file storage, email, and Malaysian payment support.
**Decision:**
- **Vercel** — hosting + Cron Jobs for serverless scheduled tasks.
- **Supabase** — managed PostgreSQL + Storage (with RLS) + Auth.
- **Resend** — transactional email delivery.
- **BillPlz** — payment gateway (Malaysia-focused, supports FPX and online banking).
**Consequences:** Serverless architecture keeps ops minimal. Supabase Storage with RLS provides secure file access without a separate media server. Cron Jobs replace a dedicated job scheduler. BillPlz webhooks require idempotent handling in the API layer.

## User Session Timeout
Sessions expire after 30 minutes of inactivity. Users are redirected to the login page upon timeout

