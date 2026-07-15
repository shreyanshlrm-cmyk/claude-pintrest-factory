#!/usr/bin/env python3
"""
Pinterest Pin Factory v5 — Buffer Edition
- Groq for text generation
- Flat-design PIL composition (no external image-gen — solid backgrounds + line-art icon)
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
PINS_PER_RUN  = 5
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
    "{topic} is one of the biggest challenges for beginners trying to build a real online income. Most people waste weeks guessing at products instead of just looking at what's already working. StoreLister gives you instant access to thousands of real ecommerce stores and their actual product catalogs — searchable and filterable by niche, so you can see exactly what's selling right now instead of guessing. Stop hunting blind and start researching like a pro. Link in bio. #dropshipping #dropshippingforbeginners #ecommerce #makemoneyonline #passiveincome #sidehustle #onlinebusiness #dropshippingtips #winningproducts #productresearch #ecommercetips #shopifydropshipping #dropshippingcoach #digitalincome #beginnerguide #storelister #dropship #onlineincome #ecommercestore #sidehustleideas #dropshippingsuccess #ecommercelife #shopify #onlinestore #competitorresearch #nichehunting #producthunting",

    "Struggling with {topic}? Most beginner dropshippers waste real money testing products that were never going to sell. StoreLister lets you browse real stores' actual catalogs, filter by niche, and see what competitors are moving before you spend a dollar on ads. It's the shortcut research pros already use. Link in bio to get access. #dropshipping #ecommerce #passiveincome #sidehustle #makemoneyonline #dropshippingforbeginners #winningproducts #shopify #productresearch #onlinebusiness #dropshippingtips #ecommercetips #digitalincome #storelister #competitoranalysis #nicheresearch #onlineincome #ecommercestore #hustleculture #dropshippingcommunity #beginnerguide #wealthbuilding #dropshipper",

    "The fastest way to find {topic} winners isn't guessing — it's seeing what real stores are already selling successfully. StoreLister gives you searchable access to thousands of live ecommerce catalogs, filtered by niche, updated daily, so you can spot untapped products and competitor gaps in minutes instead of weeks. Link in bio, $39.99/month. #dropshipping #dropshippingforbeginners #ecommerce #sidehustle #passiveincome #makemoneyonline #winningproducts #shopifydropshipping #productresearch #onlinebusiness #ecommercetips #dropshippingtips #storelister #competitorresearch #dropshippinglife #workfromhome #onlineincome #nichehunting #beginnerguide #dropshipper #ecommercestore",

    "Want to stop wasting time on {topic} and actually find products that convert? StoreLister is the largest ecom/digital product research library out there — real store data, advanced niche filters, daily updates, and competitor intelligence in one place. See what's actually selling before you build around a guess. $39.99/month, link in bio. #dropshipping #ecommerce #makemoneyonline #passiveincome #sidehustle #dropshippingforbeginners #winningproducts #shopify #productresearch #onlinebusiness #storelister #competitoranalysis #dropshippingtips #workfromhome #onlineincome #beginnerguide #nicheresearch #dropshippingcoach #dropshipper #ecommercestore",
]


# ──────────────────────────────────────────────
# GROQ TEXT GENERATION
# ──────────────────────────────────────────────

ANGLE_POOL = [
    "supplier response-time vetting",
    "small-budget ad testing methodology",
    "refund/return policy as a trust signal",
    "price-ending psychology",
    "ordering your own product to check real shipping experience",
    "spotting a saturated product before wasting money on it",
    "writing product descriptions that reduce refund requests",
    "using customer reviews to find upsell opportunities",
    "cash flow timing between ad spend and payouts",
    "packaging/unboxing as a differentiator",
    "picking a niche based on repeat-purchase potential",
    "using scarcity/urgency without looking scammy",
    "email flows for abandoned carts",
    "reading competitor reviews to find product weaknesses",
    "seasonal timing for launching a product",
    "negotiating better terms with suppliers at volume",
    "setting a kill-criteria before testing a product",
    "the real cost of chargebacks and how to reduce them",
    "using organic content to validate demand before ad spend",
    "building a repeat-customer flow instead of one-time buyers",
]

VOICE_STYLES = [
    "like a blunt friend giving you real talk, no corporate tone",
    "like a short punchy list a busy person would actually read",
    "like someone sharing a mistake they made and what they learned",
    "like a no-fluff checklist from someone who's actually done this",
]

def generate_pin_text(keyword):
    angle = random.choice(ANGLE_POOL)
    voice = random.choice(VOICE_STYLES)

    prompt = f"""You are an experienced dropshipping operator writing a Pinterest pin about: "{keyword}"

For this specific pin, ONLY write tips related to this angle: {angle}
Do not drift into generic advice outside this angle — stay specific to it.
Write {voice}.

Return ONLY valid JSON, no markdown, no backticks, no explanation:
{{
  "title": "Bold clicky headline, under 60 chars, specific to this angle, makes someone curious enough to stop scrolling",
  "seo_title": "Pinterest pin title under 100 chars, SEO optimized, includes keyword naturally",
  "tips": [
    {{"label": "3-5 word bold tip label, specific to the angle above", "text": "One sentence (max 90 chars) with a real specific number, timeframe, or mechanism"}},
    {{"label": "3-5 word bold tip label, specific to the angle above", "text": "One sentence (max 90 chars) with a real specific number, timeframe, or mechanism"}},
    {{"label": "3-5 word bold tip label, specific to the angle above", "text": "One sentence (max 90 chars) with a real specific number, timeframe, or mechanism"}}
  ]
}}

CRITICAL RULES:
- NEVER mention any brand name, "check out", "use our", or any promotional/product plug inside the tips. Pure free value, zero selling.
- Do NOT use these overused phrases, they show up too often: "verify suppliers", "test ad images", "set price floors", "optimize your listings", "leverage ads", "analyze competitors", "vet suppliers thoroughly", "price strategically".
- Each tip must sound like real specific advice someone who's actually done this would give — not a listicle template.
- No emojis anywhere."""

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
            "temperature": 1.0,
            "max_tokens": 500,
        }
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                         headers=headers, json=data, timeout=30)
        print(f"  Groq status: {r.status_code} | angle: {angle}")
        raw = r.json()

        if "choices" not in raw:
            print(f"  [Groq no 'choices'] Full response: {json.dumps(raw)[:500]}")
            raise KeyError("'choices' not in response")

        text = raw["choices"][0]["message"]["content"].strip()
        text = re.sub(r"```json|```", "", text).strip()
        parsed = json.loads(text)

        # Reject/replace any tip that slipped in a brand mention despite instructions
        banned_terms = ["rippy", "club", "check out", "use our", "join our", "storelister"]
        tips = parsed.get("tips", [])
        clean_tips = []
        rejected = 0
        for t in tips:
            combined = (t.get("label", "") + " " + t.get("text", "")).lower()
            if any(term in combined for term in banned_terms):
                rejected += 1
                continue
            clean_tips.append(t)

        if rejected:
            print(f"  [Content filter] Rejected {rejected} tip(s) for brand mention leakage")

        if len(clean_tips) < 3:
            print(f"  [Fallback triggered] Only {len(clean_tips)}/3 clean tips from Groq — padding with fallback pool")
            fallback_pool = get_fallback_tips()
            random.shuffle(fallback_pool)
            for ft in fallback_pool:
                if len(clean_tips) >= 3:
                    break
                clean_tips.append(ft)

        parsed["tips"] = clean_tips[:3]
        return parsed

    except Exception as e:
        print(f"  [Groq error] {type(e).__name__}: {e} — using fallback")
        fallback_pool = get_fallback_tips()
        random.shuffle(fallback_pool)
        return {
            "title": f"{keyword.title()}",
            "seo_title": f"{keyword.title()} — Complete Beginner Guide 2025",
            "tips": fallback_pool[:3],
        }

def get_fallback_tips():
    """A much larger, more varied fallback pool so even a Groq miss doesn't
    look repetitive across a batch of pins."""
    return [
        {"label": "Vet Supplier Response Time", "text": "Message 5 suppliers and only work with ones replying under 24 hours."},
        {"label": "Test With Small Ad Spend", "text": "Run $20-30 per product before deciding it's a loser."},
        {"label": "Watch Your Refund Policy", "text": "A clear 30-day policy reduces chargebacks more than reviews do."},
        {"label": "Price With Psychology", "text": "End prices in .97 or .99 — it measurably lifts conversion rate."},
        {"label": "Check Real Shipping Times", "text": "Order your own product first to see what customers actually experience."},
        {"label": "Read Competitor Reviews", "text": "Their 2-star reviews tell you exactly what product to launch next."},
        {"label": "Time Your Cash Flow", "text": "Don't spend on ads faster than your payout schedule can cover it."},
        {"label": "Upgrade Your Packaging", "text": "A $0.50 branded insert card doubles repeat purchase rate."},
        {"label": "Kill Criteria Before Testing", "text": "Decide your stop-loss number before you spend a single dollar."},
        {"label": "Validate With Organic First", "text": "Post the product organically for a week before paying for traffic."},
        {"label": "Negotiate At Volume", "text": "Suppliers drop prices 10-15% once you hit 50 units a month."},
        {"label": "Track Repeat Buyers", "text": "A 20% repeat rate matters more than a flashy one-time sale."},
        {"label": "Use Urgency Honestly", "text": "Real limited restocks convert better than fake countdown timers."},
        {"label": "Match Launch Timing", "text": "Give seasonal products 6 weeks of runway before the actual season."},
        {"label": "Automate Cart Recovery", "text": "A 3-email abandoned cart flow recovers 10-15% of lost sales."},
    ]

# ──────────────────────────────────────────────
# FLAT BACKGROUND — no more Pollinations/AI-art backgrounds.
# Solid cream/white tones with a subtle line-art shipping box icon.
# ──────────────────────────────────────────────

BACKGROUND_TONES = [
    (251, 249, 246),  # warm white
    (248, 244, 238),  # soft cream
    (246, 242, 234),  # light ivory
]

def generate_background_image(_unused_arg=None):
    tone = random.choice(BACKGROUND_TONES)
    img = Image.new("RGB", (PIN_WIDTH, PIN_HEIGHT), color=tone)
    draw = ImageDraw.Draw(img)
    # Much lighter/subtler now — texture, not a competing graphic
    draw_box_icon(draw, x=PIN_WIDTH - 230, y=70, size=140, color=(234, 229, 219))
    return img

def draw_box_icon(draw, x, y, size, color):
    """Simple line-art shipping box — subtle background texture that's
    actually ON-TOPIC for dropshipping, instead of generic abstract art."""
    w = size
    d = size * 0.35
    lw = 3
    top = [(x, y + d), (x + w/2, y), (x + w, y + d), (x + w/2, y + 2*d)]
    draw.line(top + [top[0]], fill=color, width=lw, joint="curve")
    draw.line([(x, y + d), (x, y + d + w*0.7), (x + w/2, y + 2*d + w*0.7), (x + w/2, y + 2*d)], fill=color, width=lw, joint="curve")
    draw.line([(x + w, y + d), (x + w, y + d + w*0.7), (x + w/2, y + 2*d + w*0.7)], fill=color, width=lw, joint="curve")
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

def draw_tracked_text(draw, text, x, y, font, color, tracking=4):
    """Draws text with extra letter-spacing (tracking) — the small detail
    that makes a kicker/label read as 'designed' rather than default."""
    cx = x
    for ch in text:
        draw.text((cx, y), ch, font=font, fill=color)
        bbox = draw.textbbox((0, 0), ch, font=font)
        cx += (bbox[2] - bbox[0]) + tracking
    return cx

def compose_pin(bg, content):
    img = bg.copy()
    draw = ImageDraw.Draw(img)

    ink = (28, 25, 22)              # near-black, warmer than pure charcoal
    accent = (128, 100, 74)         # muted mocha/taupe — calmer than the old brown
    subtext_gray = (108, 101, 92)
    circle_fg = (255, 255, 255)

    margin = 100
    max_text_width = PIN_WIDTH - (margin * 2)

    # Kicker — letter-spaced small caps, quieter and more premium than a solid block
    kicker_font = get_font(26)
    draw_tracked_text(draw, "DROPSHIPPING ADVICE", margin, 80, kicker_font, accent, tracking=5)
    draw.rectangle([(margin, 122), (margin + 70, 124)], fill=accent)  # short accent tick, not a heavy bar

    # Headline — more breathing room below the kicker
    title_font = get_font(60)
    y = draw_wrapped(draw, content["title"].upper(), margin, 175, title_font, ink, max_text_width, line_height=68)

    # Thin divider before the tips block
    y += 30
    draw.rectangle([(margin, y), (margin + max_text_width, y + 1)], fill=(224, 217, 206))
    y += 55

    # Numbered tips — filled solid circles instead of outlines
    number_font = get_font(32)
    label_font = get_font(36)
    text_font = get_font(28)

    for i, tip in enumerate(content["tips"], start=1):
        circle_d = 56
        draw.ellipse([(margin, y), (margin + circle_d, y + circle_d)], fill=accent)
        num_bbox = draw.textbbox((0, 0), str(i), font=number_font)
        nw = num_bbox[2] - num_bbox[0]
        nh = num_bbox[3] - num_bbox[1]
        draw.text((margin + circle_d/2 - nw/2, y + circle_d/2 - nh/2 - num_bbox[1]), str(i), font=number_font, fill=circle_fg)

        text_x = margin + circle_d + 32
        text_max_width = max_text_width - circle_d - 32

        label_y_end = draw_wrapped(draw, tip["label"], text_x, y - 4, label_font, ink, text_max_width, line_height=42)
        draw_wrapped(draw, tip["text"], text_x, label_y_end + 6, text_font, subtext_gray, text_max_width, line_height=34)

        y = max(label_y_end, y + circle_d) + 60

    # CTA — a slim pill instead of a heavy full-width block
    cta_font = get_font(32)
    cta_text = "Follow the link to start earning  →"
    bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    tw = bbox[2] - bbox[0]
    pad_x, pad_y = 44, 22
    pill_w = tw + pad_x * 2
    pill_h = bbox[3] - bbox[1] + pad_y * 2
    pill_x = (PIN_WIDTH - pill_w) // 2
    pill_y = PIN_HEIGHT - pill_h - 70

    draw.rounded_rectangle(
        [(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)],
        radius=pill_h // 2, fill=accent
    )
    draw.text((pill_x + pad_x, pill_y + pad_y - bbox[1]), cta_text, font=cta_font, fill=(255, 255, 255))

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

    jitter = random.randint(0, 4 * 60)  # small buffer only — the real randomness now lives in schedule_decide.py
    print(f"\n  Small start buffer: waiting {jitter // 60}m {jitter % 60}s before starting...")
    time.sleep(jitter)

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
