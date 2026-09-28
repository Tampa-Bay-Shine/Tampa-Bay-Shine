# SSL/TLS Migration Guide

## The old BookingKoala certificate does not move
The certificate currently serving https://tampabayshine.com while BookingKoala hosts the site is part of that hosting arrangement. When the public site moves to Cloudflare Pages, do not export or transfer that certificate to Cloudflare.

Cloudflare will issue/manage the certificate presented to visitors of the Cloudflare-hosted public site.

## Public site: tampabayshine.com
Cloudflare documentation says activated zones receive automatically issued and renewed public certificates. In a full DNS setup, Universal SSL normally covers the zone apex and first-level subdomains. Cloudflare Pages custom domains also require Cloudflare certificate validation/issuance as part of attaching the hostname.

Before cutover:
1. Add the domain to Cloudflare.
2. Copy and verify every DNS record.
3. Verify MX, SPF, DKIM, DMARC, email and verification records.
4. Confirm Cloudflare certificate status is active.
5. Attach tampabayshine.com and, if used, www.tampabayshine.com to the Pages project.
6. Do not change registrar nameservers until DNS inventory and staging tests are complete.

After cutover, visitors will see Cloudflare's edge certificate. The old BookingKoala apex certificate becomes irrelevant once the apex no longer routes to BookingKoala.

## BookingKoala: booking.tampabayshine.com
BookingKoala's help documentation says it supports custom domains such as bookings.yourstorename.com and that BookingKoala Support installs/updates SSL for custom domains at no charge, with up to 48 hours for processing.

Recommended sequence:
1. Ask BookingKoala Support to prepare booking.tampabayshine.com while the current apex is still live.
2. Ask BookingKoala for the exact DNS record/target.
3. Create that DNS record in Cloudflare.
4. Initially keep booking DNS-only unless BookingKoala specifically confirms Cloudflare proxying is supported.
5. Ask BookingKoala Support to install/refresh SSL for booking.tampabayshine.com.
6. Verify https://booking.tampabayshine.com in a private browser window.
7. Test login, signup, booking, recurring bookings, gift cards, referrals, password reset, customer dashboard, provider/customer links, payments, webhooks and email/SMS links.
8. Only then change the static site's transactional redirects to https://booking.tampabayshine.com/.

## Why DNS-only initially
DNS-only sends browsers directly to BookingKoala and lets BookingKoala's certificate terminate TLS. This avoids inserting Cloudflare proxy behavior into a third-party SaaS custom-domain setup before BookingKoala confirms compatibility.

## BookingKoala support request template
Subject: Add booking.tampabayshine.com custom domain and SSL

Hello BookingKoala Support,

We are moving our public marketing website at https://tampabayshine.com to Cloudflare Pages, but we will continue using BookingKoala for booking, customer login, gift cards, referrals, account functions, and transactional workflows.

Please add/prepare the custom hostname:
https://booking.tampabayshine.com

Please send me the exact DNS record and target I should create.

I also need BookingKoala to install/update the SSL certificate for booking.tampabayshine.com.

For migration safety, please confirm whether:
1. booking.tampabayshine.com can be added while tampabayshine.com is still the current BookingKoala custom domain;
2. adding it will affect current customer/provider sessions or existing links;
3. Google/Facebook OAuth callback URLs, webhook URLs, payment settings, notification links, or other integrations need updates;
4. the DNS record should remain DNS-only in Cloudflare, or whether proxying is supported.

Please do not remove or disrupt the current tampabayshine.com configuration until I confirm final cutover.

Thank you.
