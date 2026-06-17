# Project Wiki

## Architecture Overview

## Tech Stack

### Vercel
- **Purpose:** Hosting platform for the web application and API routes.
- **Key features used:** Serverless Functions, Edge Functions, and preview deployments.
- **Vercel Cron Jobs:** Scheduled serverless function invocations for recurring tasks (e.g., daily cleanup, periodic syncs). Configured via \vercel.json\ with the \crons\ property.
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

## Key Decisions

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

