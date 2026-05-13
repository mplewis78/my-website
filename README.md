# Mike Lewis — Coaching Site

Static HTML site. No build step.

## Pages

- `index.html` — Home (was `home.html` in development)
- `my-background.html` — Background, ETW, career, LinkedIn
- `work-with-me.html` — Engagement details, the hike intro
- `companies.html` — Quotes, video placeholders, case studies
- `writing.html` — Mike & Ned's Links (Substack) + blog posts
- `contact.html` — Contact form

## Shared files

- `site.css` — All shared styling (palette, type, nav, footer, etc.)
- `site.js` — Nav scroll behavior, mobile drawer, reveal-on-scroll, etc.
- `image-slot.js` — Web component powering the drag-and-drop image placeholders. **Drop your photos directly onto the slots in the live page** — state persists in `localStorage`. When you're ready to make the photos permanent, replace each `<image-slot>` element with a normal `<img src="...">`.

## Hosting on GitHub Pages

1. Push the contents of this folder to the root of a repository.
2. In repo Settings → Pages, set Source to "Deploy from a branch", branch `main`, folder `/ (root)`.
3. Visit `https://<your-username>.github.io/<repo-name>/`.

## Custom domain

If you're pointing `mikelewis.me` here later:
1. Add a `CNAME` file at the root containing just `mikelewis.me`
2. Configure DNS at your registrar (ALIAS/ANAME → `<username>.github.io`, or A records to GitHub Pages IPs)
3. Set custom domain in repo Settings → Pages

## Known placeholders to swap

- All image-slots (drop real photos in the live page)
- Founder names/photos on `companies.html` case studies and video cards
- Founder face slots on the Companies quotes (LinkedIn endorsements are real, photos are still empty)
- Recent Mike & Ned issue titles on `writing.html` (currently labeled "Issue #109 / 108 / 107 / 106" linking to Substack — replace with real titles when you wire it up)
- `hello@mikelewis.co` in footer — confirm the right email

## License

© 2026 Mike Lewis. All rights reserved.
