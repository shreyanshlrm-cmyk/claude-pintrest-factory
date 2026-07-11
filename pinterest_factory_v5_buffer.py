#!/usr/bin/env python3
"""
Pinterest Pin Factory v5 — Buffer Edition
- Groq for text generation
- Pollinations.ai for background images
- PIL for branded overlay composition
- Images hosted via this repo (committed + pushed, served via raw.githubusercontent.com)
- Buffer GraphQL API for actual Pinterest publishing (no Pinterest dev app needed)
"""

import os
import re
import json
import time
import random
import subprocess
import requests
import textwrap
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from datetime import datetime

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────

GROQ_API_KEY      = os.environ.get("GROQ_API_KEY")
AFFILIATE_LINK    = os.environ.get("AFFILIATE_LINK")
BUFFER_API_KEY    = os.environ.get("BUFFER_API_KEY")
BUFFER_CHANNEL_ID = os.environ.get("BUFFER_CHANNEL_ID")
BUFFER_BOARD_ID   = os.environ.get("BUFFER_BOARD_ID")

GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")  # e.g. "shreyanshlrm-cmyk/pinterest-factory", auto-set by Actions
GITHUB_REF_NAME    = os.environ.get("GITHUB_REF_NAME", "main")

OUTPUT_DIR    = "hosted_pins"
PINS_PER_RUN  = 10
PIN_WIDTH     = 1000
PIN_HEIGHT    = 1500

BUFFER_API_URL = "https://api.buffer.com"

# ──────────────────────────────────────────────
# KEYWORD POOL
# ──────────────────────────────────────────────

KEYWORD_POOL = [
    "how to start dropshipping 2025",
    "dropshipping for beginners step by step",
    "best dropshipping products to sell 2025",
    "how to find winning dropshipping products",
    "dropshipping product research tutorial",
    "how to make first sale dropshipping",
    "dropshipping supplier guide for beginners",
    "how to build a dropshipping store from scratch",
    "dropshipping mistakes beginners make",
    "how to scale a dropshipping business",
    "best dropshipping niches 2025",
    "dropshipping vs amazon fba which is better",
    "how to do dropshipping with no money",
    "dropshipping tips that actually work",
    "how to find dropshipping products that sell",
    "rippy club dropshipping community review",
    "best dropshipping community for beginners",
    "dropshipping mentorship and coaching",
    "learn dropshipping with weekly live classes",
    "dropshipping done for you product research",
    "how to make passive income with dropshipping",
    "ecommerce side hustle for beginners 2025",
    "how to make money online with ecommerce",
    "passive income ideas that actually work 2025",
    "how to escape 9 to 5 with dropshipping",
    "online business ideas for beginners 2025",
    "how to build wealth with ecommerce",
    "make money online dropshipping guide",
    "financial freedom through dropshipping",
    "side hustle ideas that make real money",
    "how to start ecommerce business 2025",
    "dropshipping success stories beginners",
    "how to find hot products to dropship",
    "dropshipping shopify tutorial for beginners",
    "winning products dropshipping 2025",
    "how to get dropshipping sales fast",
    "dropshipping product testing strategy",
    "how to pick a dropshipping niche",
    "dropshipping marketing strategies 2025",
    "how to run ads for dropshipping beginners",
]

DESCRIPTION_TEMPLATES = [
    "{topic} is one of the most searched topics for beginners trying to build an online income in 2025. Most people fail because they're trying to figure it out alone without the right systems, product research, or community. Rippy Club is the #1 all-in-one dropshipping hub with 500+ active members, 2 live coaching classes every week, 100s of hours of recorded tutorials on every dropshipping topic, weekly winning product research drops, direct access to top ecommerce entrepreneurs, and a beginner-friendly community that actually helps you grow. Link in bio to join. #dropshipping #dropshippingforbeginners #ecommerce #makemoneyonline #passiveincome #sidehustle #onlinebusiness #dropshippingtips #winningproducts #ecommercetips #dropshippinglife #shopifydropshipping #productresearch #dropshippingcoach #financialfreedom #workfromhome #digitalincome #dropshippingcommunity #beginnerguide #rippyclub",

    "Struggling with {topic}? You're not alone — most beginner dropshippers waste months trying to figure this out without any guidance. Rippy Club gives you 2 live classes weekly, hundreds of hours of ecommerce tutorials, done-for-you product research, case studies from real sellers, and direct access to top entrepreneurs in the space. 500+ members are already inside building their stores. Link in bio. #dropshipping #ecommerce #passiveincome #sidehustle #makemoneyonline #dropshippingforbeginners #winningproducts #shopify #productresearch #onlinebusiness #dropshippingtips #ecommercetips #financialfreedom #workfromhome #dropshippingcommunity #rippyclub",

    "The fastest way to learn {topic} is not watching YouTube videos alone — it's being inside a community of people actively doing it with you. Rippy Club is built for beginner and intermediate dropshippers who want real results. Inside you get weekly winning product drops, 2 live coaching classes every week, 100s of hours of recorded classes, case studies, and direct access to successful ecommerce entrepreneurs. Link in bio, $50/month. #dropshipping #dropshippingforbeginners #ecommerce #sidehustle #passiveincome #makemoneyonline #winningproducts #shopifydropshipping #productresearch #onlinebusiness #ecommercetips #dropshippingtips #financialfreedom #rippyclub #dropshippingcommunity",

    "Want to master {topic} without wasting months of trial and error? Rippy Club is the #1 dropshipping hub on the internet with 500+ members, weekly winning product drops, 2 live classes every week, 100s of hours of tutorials, real case studies, and direct access to top ecom entrepreneurs. $50 a month. Link in bio. #dropshipping #ecommerce #makemoneyonline #passiveincome #sidehustle #dropshippingforbeginners #winningproducts #shopify #productresearch #onlinebusiness #financialfreedom #rippyclub #dropshippingcommunity #ecommercetips #dropshippingtips",
]

IMAGE_STYLE_POOL = [
    "clean white marble background, soft natural light, calm premium aesthetic, subtle beige and cream tones, no text, minimalist, high quality, editorial photography style",
    "soft ivory and white background, gentle warm light, airy premium feel, subtle linen texture, no text, clean, elegant, high quality",
    "pale cream background with soft shadows, minimal luxury aesthetic, subtle gold thread details, no text, calm and refined, high quality",
    "white studio background with soft diffused light, modern premium aesthetic, subtle beige gradient, no text, clean, professional",
    "light neutral background, soft morning light, calm and grounded premium feel, subtle warm undertones, no text, high quality, sharp",
    "off-white textured background, gentle natural shadows, quiet luxury aesthetic, no text, minimal, high quality, soft focus edges",
    "soft white and champagne gradient background, calm elegant aesthetic, subtle light rays, no text, clean, premium, polished",
]

# ──────────────────────────────────────────────
# GROQ TEXT GENERATION
# ──────────────────────────────────────────────

def generate_pin_text(keyword):
    prompt = f"""You are an experienced dropshipping operator writing genuinely useful Pinterest tips on: "{keyword}"

Return ONLY valid JSON, no markdown, no backticks, no explanation:
{{
  "title": "Bold clicky headline, under 60 chars, makes dropshippers curious about money/results, includes or implies the keyword topic",
  "seo_title": "Pinterest pin title under 100 chars, SEO optimized, includes keyword naturally",
  "tips": [
    {{"label": "3-5 word bold tip label", "text": "One short sentence (max 90 chars) expanding on the tip"}},
    {{"label": "3-5 word bold tip label", "text": "One short sentence (max 90 chars) expanding on the tip"}},
    {{"label": "3-5 word bold tip label", "text": "One short sentence (max 90 chars) expanding on the tip"}}
  ]
}}

CRITICAL RULES for the 3 tips:
- Each tip must be genuinely actionable, specific dropshipping advice a real operator would give — something someone could actually go do today.
- NEVER mention Rippy Club, any brand name, "check out", "use our", or any promotional/product plug inside the tips. The tips are pure free value, zero selling.
- Avoid vague generic filler like "optimize your listings" or "leverage ads" with no specifics — give a concrete mechanism, number, tool category, or method instead.
- Vary the angle across pins: sometimes about supplier vetting, sometimes ad testing methodology, sometimes pricing psychology, sometimes customer service, sometimes niche selection criteria, sometimes cash flow / return policy specifics — don't default to the same 3 tips every time.
- No emojis anywhere.

The headline can hint at a bigger opportunity, but the 3 tips themselves must stand alone as real, specific, useful advice with no brand mention."""

    try:
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set or empty")

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.85,
            "max_tokens": 500,
        }
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                         headers=headers, json=data, timeout=30)
        print(f"  Groq status: {r.status_code}")
        raw = r.json()

        if "choices" not in raw:
            print(f"  [Groq no 'choices'] Full response: {json.dumps(raw)[:500]}")
            raise KeyError("'choices' not in response")

        text = raw["choices"][0]["message"]["content"].strip()
        text = re.sub(r"```json|```", "", text).strip()
        parsed = json.loads(text)

        # Reject/replace any tip that slipped in a brand mention despite instructions
        banned_terms = ["rippy", "club", "check out", "use our", "join our"]
        tips = parsed.get("tips", [])
        clean_tips = []
        for t in tips:
            combined = (t.get("label", "") + " " + t.get("text", "")).lower()
            if any(term in combined for term in banned_terms):
                continue
            clean_tips.append(t)

        fallback_pool = [
            {"label": "Vet Supplier Response Time", "text": "Message 5 suppliers and only work with ones replying under 24 hours."},
            {"label": "Test With Small Ad Spend", "text": "Run $20-30 per product before deciding it's a loser."},
            {"label": "Watch Your Refund Policy", "text": "A clear 30-day policy reduces chargebacks more than reviews do."},
            {"label": "Price With Psychology", "text": "End prices in .97 or .99 — it measurably lifts conversion rate."},
            {"label": "Check Real Shipping Times", "text": "Order your own product first to see what customers actually experience."},
        ]
        while len(clean_tips) < 3:
            clean_tips.append(random.choice(fallback_pool))

        parsed["tips"] = clean_tips[:3]
        return parsed

    except Exception as e:
        print(f"  [Groq error] {e} — using fallback")
        return {
            "title": f"{keyword.title()}",
            "seo_title": f"{keyword.title()} — Complete Beginner Guide 2025",
            "tips": [
                {"label": "Vet Supplier Response Time", "text": "Message 5 suppliers and only work with ones replying under 24 hours."},
                {"label": "Test With Small Ad Spend", "text": "Run $20-30 per product before deciding it's a loser."},
                {"label": "Watch Your Refund Policy", "text": "A clear 30-day policy reduces chargebacks more than reviews do."},
            ],
        }

# ──────────────────────────────────────────────
# FLAT BACKGROUND — no more Pollinations/AI-art backgrounds.
# Solid cream/white tones with a subtle line-art shipping box icon.
# ──────────────────────────────────────────────

BACKGROUND_TONES = [
    (250, 248, 244),  # warm white
    (247, 243, 236),  # soft cream
    (245, 241, 232),  # light ivory
]

def generate_background_image(_unused_arg=None):
    tone = random.choice(BACKGROUND_TONES)
    img = Image.new("RGB", (PIN_WIDTH, PIN_HEIGHT), color=tone)
    draw = ImageDraw.Draw(img)
    draw_box_icon(draw, x=PIN_WIDTH - 260, y=90, size=170, color=(225, 218, 205))
    return img

def draw_box_icon(draw, x, y, size, color):
    """Simple line-art shipping box — subtle background texture that's
    actually ON-TOPIC for dropshipping, instead of generic abstract art."""
    w = size
    d = size * 0.35  # depth offset for the 3D look
    lw = 4
    # top face (diamond)
    top = [(x, y + d), (x + w/2, y), (x + w, y + d), (x + w/2, y + 2*d)]
    draw.line(top + [top[0]], fill=color, width=lw, joint="curve")
    # front-left face
    draw.line([(x, y + d), (x, y + d + w*0.7), (x + w/2, y + 2*d + w*0.7), (x + w/2, y + 2*d)], fill=color, width=lw, joint="curve")
    # front-right face
    draw.line([(x + w, y + d), (x + w, y + d + w*0.7), (x + w/2, y + 2*d + w*0.7)], fill=color, width=lw, joint="curve")
    # tape line down the middle front
    draw.line([(x + w/2, y + 2*d), (x + w/2, y + 2*d + w*0.7)], fill=color, width=lw)

# ──────────────────────────────────────────────
# PIN COMPOSER — flat design, numbered tips layout
# ──────────────────────────────────────────────

def get_font(size, bold=True):
    bold_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]
    regular_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for p in (bold_paths if bold else regular_paths):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                continue
    return ImageFont.load_default()

def wrap_by_pixel_width(draw, text, font, max_width):
    """Wraps text based on ACTUAL measured pixel width, not an estimate —
    prevents text overflowing off the edge of the canvas."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

def draw_wrapped(draw, text, x, y, font, color, max_width, line_height=None, align="left"):
    """Draws left-aligned (or centered) wrapped text starting at (x, y). Returns the y position after the block."""
    lines = wrap_by_pixel_width(draw, text, font, max_width)
    lh = line_height or (font.size + 10)
    cy = y
    for line in lines:
        draw_x = x
        if align == "center":
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            draw_x = x - tw // 2
        draw.text((draw_x, cy), line, font=font, fill=color)
        cy += lh
    return cy

def compose_pin(bg, content):
    img = bg.copy()
    draw = ImageDraw.Draw(img)

    charcoal = (35, 30, 25)
    accent = (150, 110, 60)   # warm brown/gold accent for numbers + CTA
    subtext_gray = (90, 85, 78)

    margin = 90
    max_text_width = PIN_WIDTH - (margin * 2)

    # Kicker
    kicker_font = get_font(30)
    draw.text((margin, 70), "DROPSHIPPING ADVICE", font=kicker_font, fill=accent)
    draw.rectangle([(margin, 112), (margin + 260, 115)], fill=accent)

    # Headline
    title_font = get_font(64)
    y = draw_wrapped(draw, content["title"].upper(), margin, 150, title_font, charcoal, max_text_width, line_height=70)

    # Numbered tips
    y += 40
    number_font = get_font(46)
    label_font = get_font(38)
    text_font = get_font(30)

    for i, tip in enumerate(content["tips"], start=1):
        circle_d = 64
        draw.ellipse([(margin, y), (margin + circle_d, y + circle_d)], outline=accent, width=4)
        num_bbox = draw.textbbox((0, 0), str(i), font=number_font)
        nw = num_bbox[2] - num_bbox[0]
        nh = num_bbox[3] - num_bbox[1]
        draw.text((margin + circle_d/2 - nw/2, y + circle_d/2 - nh/2 - num_bbox[1]), str(i), font=number_font, fill=accent)

        text_x = margin + circle_d + 30
        text_max_width = max_text_width - circle_d - 30

        label_y_end = draw_wrapped(draw, tip["label"], text_x, y, label_font, charcoal, text_max_width, line_height=44)
        draw_wrapped(draw, tip["text"], text_x, label_y_end + 4, text_font, subtext_gray, text_max_width, line_height=36)

        y = max(label_y_end, y + circle_d) + 55

    # CTA banner at the bottom
    banner_h = 140
    banner_y = PIN_HEIGHT - banner_h
    draw.rectangle([(0, banner_y), (PIN_WIDTH, PIN_HEIGHT)], fill=accent)
    cta_font = get_font(38)
    cta_text = "Follow the link to start earning"
    bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    tw = bbox[2] - bbox[0]
    draw.text(((PIN_WIDTH - tw) // 2, banner_y + banner_h//2 - 20), cta_text, font=cta_font, fill=(255, 255, 255))

    return img

# ──────────────────────────────────────────────
# GENERATE ALL PINS
# ──────────────────────────────────────────────

def generate_pins():
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    keywords = random.sample(KEYWORD_POOL, min(PINS_PER_RUN, len(KEYWORD_POOL)))
    pins = []

    for i, kw in enumerate(keywords, 1):
        print(f"\n[Pin {i}/{PINS_PER_RUN}] {kw}")
        content = generate_pin_text(kw)
        bg = generate_background_image()
        img = compose_pin(bg, content)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        fname = f"pin_{i:02d}_{ts}.jpg"
        fpath = os.path.join(OUTPUT_DIR, fname)
        img.save(fpath, "JPEG", quality=90)
        print(f"  Saved: {fpath}")

        desc = random.choice(DESCRIPTION_TEMPLATES).format(
            topic=kw.replace("how to ","").replace("best ","").title()
        )

        pins.append({
            "filepath":    fpath,
            "filename":    fname,
            "title":       content["seo_title"],
            "description": desc,
            "link":        AFFILIATE_LINK,
        })
        time.sleep(1)

    return pins

# ──────────────────────────────────────────────
# COMMIT + PUSH IMAGES SO THEY HAVE PUBLIC URLS
# ──────────────────────────────────────────────

def wait_for_url_ready(url, max_attempts=8, delay=5):
    """raw.githubusercontent.com doesn't serve a freshly pushed file instantly —
    poll until it actually returns 200 before handing the URL to Buffer."""
    for attempt in range(1, max_attempts + 1):
        try:
            r = requests.head(url, timeout=15, allow_redirects=True)
            if r.status_code == 200:
                return True
            print(f"    [waiting for image to propagate] attempt {attempt}/{max_attempts}, got {r.status_code}")
        except Exception as e:
            print(f"    [waiting for image to propagate] attempt {attempt}/{max_attempts}, error: {e}")
        time.sleep(delay)
    return False

def commit_and_push_images(pins):
    print("\n[Hosting] Committing pin images to repo for public URLs...")
    subprocess.run(["git", "config", "user.name", "pinterest-factory-bot"], check=True)
    subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
    subprocess.run(["git", "add", OUTPUT_DIR], check=True)

    result = subprocess.run(["git", "commit", "-m", "Add daily pin images"], capture_output=True, text=True)
    print(result.stdout, result.stderr)

    subprocess.run(["git", "push"], check=True)

    # Build the public raw URL for each pin's image
    for pin in pins:
        pin["image_url"] = (
            f"https://raw.githubusercontent.com/{GITHUB_REPOSITORY}/"
            f"{GITHUB_REF_NAME}/{OUTPUT_DIR}/{pin['filename']}"
        )

    print("  Images pushed. Verifying each URL is actually live before uploading...")
    for pin in pins:
        ready = wait_for_url_ready(pin["image_url"])
        if ready:
            print(f"  Ready: {pin['filename']}")
        else:
            print(f"  [WARNING] {pin['filename']} never became reachable — upload will likely fail")

# ──────────────────────────────────────────────
# BUFFER UPLOAD
# ──────────────────────────────────────────────

def buffer_gql(query, variables=None):
    r = requests.post(
        BUFFER_API_URL,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {BUFFER_API_KEY}",
        },
        json={"query": query, "variables": variables or {}},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()

def truncate_for_pinterest(text, limit=500):
    if len(text) <= limit:
        return text
    cut = text[:limit]
    last_space = cut.rfind(" ")
    if last_space > 0:
        cut = cut[:last_space]
    return cut

def create_pin_on_buffer(pin):
    query = """
    mutation CreatePin($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post { id dueAt }
        }
        ... on MutationError {
          message
        }
      }
    }
    """
    variables = {
        "input": {
            "channelId": BUFFER_CHANNEL_ID,
            "text": truncate_for_pinterest(pin["description"]),
            "assets": [
                {
                    "image": {
                        "url": pin["image_url"],
                        "metadata": {
                            "altText": pin["title"][:100]
                        }
                    }
                }
            ],
            "schedulingType": "automatic",
            "mode": "shareNow",   # publish immediately instead of queueing
            "metadata": {
                "pinterest": {
                    "boardServiceId": BUFFER_BOARD_ID,
                    "title": pin["title"][:100],
                    "url": pin["link"],
                    # NOTE: Buffer's own roadmap/known-issues page (as of mid-2026) states
                    # this "url" field is currently accepted but NOT persisted/saved on
                    # their backend for Pinterest posts — a bug on Buffer's side, not ours.
                    # Pins may post successfully without the destination link attached
                    # until Buffer fixes this. Worth checking pins manually until then.
                }
            },
        }
    }

    resp = buffer_gql(query, variables)

    if "errors" in resp and resp["errors"]:
        print(f"  [Buffer error] {resp['errors'][0].get('message')}")
        return False

    result = resp.get("data", {}).get("createPost", {})
    if result.get("post"):
        print(f"  Pin posted! id={result['post']['id']}")
        return True
    else:
        print(f"  [Pin failed] {result.get('message')}")
        return False

def upload_all(pins):
    print("\n" + "=" * 50)
    print("  UPLOADING TO PINTEREST (via Buffer API)")
    print("=" * 50)

    if not all([BUFFER_API_KEY, BUFFER_CHANNEL_ID, BUFFER_BOARD_ID]):
        print("  Missing one or more required env vars: "
              "BUFFER_API_KEY, BUFFER_CHANNEL_ID, BUFFER_BOARD_ID")
        return

    success = 0
    for i, pin in enumerate(pins, 1):
        print(f"\n[Upload {i}/{len(pins)}] {pin['title'][:50]}")
        if create_pin_on_buffer(pin):
            success += 1
        time.sleep(2)  # small courtesy delay between calls

    print(f"\n  Done: {success}/{len(pins)} posted")

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    print("=" * 50)
    print(f"  PINTEREST FACTORY v5 — BUFFER EDITION")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    print(f"\n  GROQ_API_KEY set: {'YES' if GROQ_API_KEY else 'NO'}")
    print(f"  AFFILIATE_LINK set: {'YES' if AFFILIATE_LINK else 'NO'}")
    print(f"  BUFFER_API_KEY set: {'YES' if BUFFER_API_KEY else 'NO'}")
    print(f"  BUFFER_CHANNEL_ID set: {'YES' if BUFFER_CHANNEL_ID else 'NO'}")
    print(f"  BUFFER_BOARD_ID set: {'YES' if BUFFER_BOARD_ID else 'NO'}")
    print(f"  Repo: {GITHUB_REPOSITORY} @ {GITHUB_REF_NAME}")

    print("\n[1/3] Generating pins...")
    pins = generate_pins()
    print(f"  {len(pins)} pins ready")

    print("\n[2/3] Hosting images via repo...")
    commit_and_push_images(pins)

    print("\n[3/3] Uploading to Pinterest via Buffer...")
    upload_all(pins)

    print("\n  All done. See you tomorrow.")

if __name__ == "__main__":
    main()
