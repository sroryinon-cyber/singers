#!/usr/bin/env python3
"""בונה עמוד לכל זמר מתוך singers.json + template.html אל התיקייה docs/.
תמונות שמים ב-docs/images, סרטונים (mp4 מכווץ) ב-docs/videos.

הרצה:  python3 build.py
"""
import json
import shutil
from html import escape
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
DIST = ROOT / "docs"  # GitHub Pages מגיש את האתר מהתיקייה docs

PLAY_ICON = '<span class="play"><svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M6 3.5v13a.7.7 0 001.06.6l10.4-6.5a.7.7 0 000-1.2L7.06 2.9A.7.7 0 006 3.5z"/></svg></span>'


def video_card(video, singer, index):
    """כרטיס סרטון.

    file + poster  – קובץ mp4 ותמונה מתוך docs/videos ו-docs/images (מתנגן מיד, מומלץ)
    driveId        – סרטון מגוגל דרייב (איטי יותר)
    embedUrl+thumb – נגן מוטמע מכל אחסון אחר
    """
    kind = "embed"
    if video.get("file"):
        kind = "video"
        src = "../videos/" + quote(video["file"])
        thumb = "../images/" + quote(video["poster"]) if video.get("poster") else ""
    elif video.get("driveId"):
        vid = quote(video["driveId"], safe="")
        src = f"https://drive.google.com/file/d/{vid}/preview"
        thumb = f"https://drive.google.com/thumbnail?id={vid}&sz=w720"
    else:
        src = video["embedUrl"]
        thumb = video.get("thumb", "")

    title = video.get("title", "").strip()
    label = f'{singer["name"]} – {title}' if title else f'{singer["name"]} – סרטון {index + 1}'
    classes = "video featured" if video.get("featured") else "video"
    img = (
        f'<img src="{escape(thumb, quote=True)}" alt="" loading="lazy" referrerpolicy="no-referrer">'
        if thumb
        else ""
    )
    caption = f'<span class="video-title">{escape(title)}</span>' if title else ""
    return (
        f'      <button type="button" class="{classes}" data-kind="{kind}" data-src="{escape(src, quote=True)}" '
        f'aria-label="{escape(label, quote=True)}">{img}{PLAY_ICON}{caption}</button>'
    )


def render(template, site, singer):
    # סרטון אחד מודגש למעלה (featured), השאר בשורה שגוללים הצידה
    videos = sorted(singer["videos"], key=lambda v: not v.get("featured"))
    for extra in videos[1:]:
        extra.pop("featured", None)
    cards = [video_card(v, singer, i) for i, v in enumerate(videos)]
    featured_html, rest_html = "", ""
    if videos and videos[0].get("featured"):
        featured_html = f'    <div class="featured-wrap">\n{cards.pop(0)}\n    </div>'
    if cards:
        rest_html = '    <div class="videos">\n' + "\n".join(cards) + "\n    </div>"

    tagline = singer.get("tagline", "").strip()
    about = singer.get("about", "").strip()
    quotes = singer.get("testimonials", [])

    about_html = (
        f'  <section class="about wrap">\n    <h2>כמה מילים על <span>{escape(singer["firstName"])}</span></h2>\n'
        f"    <p>{escape(about)}</p>\n  </section>"
        if about
        else ""
    )
    quotes_html = ""
    if quotes:
        items = "\n".join(
            f'      <blockquote class="quote"><p>{escape(q["text"])}</p>'
            f'<footer>{escape(q.get("by", ""))}</footer></blockquote>'
            for q in quotes
        )
        quotes_html = (
            '  <section class="wrap">\n    <h2>זוגות <span>מספרים</span></h2>\n'
            f'    <div class="quotes">\n{items}\n    </div>\n  </section>'
        )

    site_url = site.get("siteUrl", "").rstrip("/")
    og_image = (
        f'<meta property="og:image" content="{escape(site_url, quote=True)}/images/{escape(singer["photo"], quote=True)}">\n'
        f'<meta property="og:url" content="{escape(site_url, quote=True)}/{escape(singer["slug"], quote=True)}/">'
        if site_url
        else ""
    )

    values = {
        "name": escape(singer["name"]),
        "firstName": escape(singer["firstName"]),
        "band": escape(site["band"]),
        "photo": escape(singer["photo"], quote=True),
        "photoFocus": escape(singer.get("photoFocus", "50% 30%"), quote=True),
        "tagline": f'<p class="tagline">{escape(tagline)}</p>' if tagline else "",
        "featured": featured_html,
        "videos": rest_html,
        "about": about_html,
        "testimonials": quotes_html,
        "ogImage": og_image,
    }
    html = template
    for key, value in values.items():
        html = html.replace("{{" + key + "}}", value)
    return html


def main():
    data = json.loads((ROOT / "singers.json").read_text(encoding="utf-8"))
    template = (ROOT / "template.html").read_text(encoding="utf-8")
    site = data["site"]

    # התמונות והסרטונים יושבים ישירות ב-docs/images וב-docs/videos ולא נמחקים בבנייה.
    # רק תיקיות העמודים נבנות מחדש.
    DIST.mkdir(exist_ok=True)
    for old in DIST.iterdir():
        if old.is_dir() and old.name not in ("images", "videos"):
            shutil.rmtree(old)

    for singer in data["singers"]:
        out = DIST / singer["slug"]
        out.mkdir()
        (out / "index.html").write_text(render(template, site, singer), encoding="utf-8")
        print(f'נבנה: /{singer["slug"]}/')

    # עמוד הבית ריק בכוונה: אין רשימת זמרים, מגיעים רק דרך לינק אישי
    (DIST / "index.html").write_text(
        '<!doctype html><html lang="he" dir="rtl"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta name="robots" content="noindex, nofollow">'
        f'<title>להקת {escape(site["band"])}</title>'
        '<body style="margin:0;min-height:100vh;display:grid;place-items:center;background:#0b0d10;'
        f'color:#f4f1ea;font-family:system-ui,sans-serif"><p>להקת {escape(site["band"])}</p></body></html>',
        encoding="utf-8",
    )
    (DIST / ".nojekyll").write_text("", encoding="utf-8")
    (DIST / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")


if __name__ == "__main__":
    main()
