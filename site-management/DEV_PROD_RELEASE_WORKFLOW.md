
# Phase 2.5.8 — BookingKoala fallback release mode

Production transaction traffic is temporarily sent to:

    https://tampabayshine.bookingkoala.com

The future custom BK host remains:

    https://booking.tampabayshine.com

The custom host is monitored but does not block a fallback-mode release.

## Critical safety requirement

Before moving `tampabayshine.com` to Cloudflare, make the original BookingKoala-hosted domain
`tampabayshine.bookingkoala.com` the BookingKoala **Primary** domain if BookingKoala allows it.

Why: BookingKoala says its Primary domain is used for dashboards and links in system email/SMS
notifications. If the apex remains BK Primary after the apex is moved to Cloudflare, generated deep
links may point at Cloudflare rather than BookingKoala.

After changing BK Primary to the fallback domain, test admin login, customer login, provider app/session,
recurring jobs, an actual email notification from owner@tampabayshine.com, a link inside that email,
and an SMS notification link. Then set the corresponding manual gates to true.

## Gate

    python.exe .\tools\migration_gate.py --repo . --phase staging

## Promotion

Dry preparation only:

    python.exe .\tools\promote_cloudflare.py --repo .

Actual production branch push:

    python.exe .\tools\promote_cloudflare.py --repo . --push

## Later switch to custom booking domain

    python.exe .\tools\set_transaction_mode.py custom --repo .
    git add site-management\release_targets.json
    git commit -m "Switch production transactions to booking subdomain"
    git push

Then rerun the staging gate and promote normally.

## Dev / production separation

Development stays on Cloudflare project `tampa-bay-shine-staging`, branch `cloudflare-staging`.
Production stays on Cloudflare project `tampa-bay-shine`, branch `cloudflare-production`.
Normal development pushes do not change production.
