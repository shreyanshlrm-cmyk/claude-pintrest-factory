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
    prompt = f"""You are a Pinterest SEO expert for a dropshipping affiliate page promoting Rippy Club.
Generate content for a Pinterest pin targeting: "{keyword}"

Return ONLY valid JSON, no markdown, no backticks, no explanation:
{{
  "title": "Pinterest pin title under 100 chars, SEO optimized, includes keyword naturally, compelling",
  "hook": "6-8 word bold statement for image text overlay, no emojis, punchy and stops the scroll"
}}

Rules:
- Title must feel helpful and searchable
- Hook must make someone stop scrolling instantly
- No emojis anywhere
- Keep it direct and specific"""

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
            "temperature": 0.7,
            "max_tokens": 200,
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
        return json.loads(text)

    except Exception as e:
        print(f"  [Groq error] {e} — using fallback")
        return {
            "title": f"{keyword.title()} — Complete Beginner Guide 2025",
            "hook": "Most beginners never learn this",
        }

# ──────────────────────────────────────────────
# IMAGE GENERATION — Pollinations.ai
# ──────────────────────────────────────────────

def generate_background_image(style_prompt):
    encoded = requests.utils.quote(style_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={PIN_WIDTH}&height={PIN_HEIGHT}&nologo=true&seed={random.randint(1,99999)}"
    try:
        print("  Generating image...")
        r = requests.get(url, timeout=60)
        if r.status_code == 200:
            Path(OUTPUT_DIR).mkdir(exist_ok=True)
            temp = f"{OUTPUT_DIR}/temp_{random.randint(1000,9999)}.jpg"
            with open(temp, "wb") as f:
                f.write(r.content)
            img = Image.open(temp).convert("RGB")
            os.remove(temp)
            return img
    except Exception as e:
        print(f"  [Pollinations error] {e}")
    return Image.new("RGB", (PIN_WIDTH, PIN_HEIGHT), color=(15, 15, 25))

# ──────────────────────────────────────────────
# PIN COMPOSER
# ──────────────────────────────────────────────

def add_overlay(img):
    # Lighter overlay now since background is white/cream — a heavy dark
    # overlay would defeat the calm premium look. Just a soft white wash
    # for text contrast instead.
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 60))
    img = img.convert("RGBA")
    return Image.alpha_composite(img, overlay).convert("RGB")

def get_font(size):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for p in paths:
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

def draw_centered(draw, text, y, font, color=(30,30,30), max_width=820):
    lines = wrap_by_pixel_width(draw, text, font, max_width)
    lh = font.size + 14
    total = len(lines) * lh
    cy = y - total // 2
    for line in lines:
        bbox = draw.textbbox((0,0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (PIN_WIDTH - tw) // 2
        draw.text((x+1, cy+1), line, font=font, fill=(255,255,255))  # soft light shadow instead of black
        draw.text((x, cy), line, font=font, fill=color)
        cy += lh

def compose_pin(bg, hook_text):
    img = add_overlay(bg.copy())
    draw = ImageDraw.Draw(img)
    charcoal = (60, 50, 40)
    draw_centered(draw, "DROPSHIPPING ADVICE", 120, get_font(34), color=charcoal, max_width=780)
    draw.rectangle([(140,152),(PIN_WIDTH-140,155)], fill=charcoal)
    draw_centered(draw, hook_text.upper(), PIN_HEIGHT//2 - 60, get_font(58), color=(20,20,20), max_width=780)
    draw.rectangle([(140,PIN_HEIGHT-222),(PIN_WIDTH-140,PIN_HEIGHT-219)], fill=charcoal)
    draw_centered(draw, "Follow the link to earn", PIN_HEIGHT-160, get_font(40), color=charcoal, max_width=780)
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
        pin_text = generate_pin_text(kw)
        bg = generate_background_image(random.choice(IMAGE_STYLE_POOL))
        img = compose_pin(bg, pin_text["hook"])

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
            "title":       pin_text["title"],
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
