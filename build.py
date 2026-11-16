#!/usr/bin/env python3
"""בונה עמוד לכל זמר מתוך singers.json + template.html אל התיקייה docs/.

הרצה:  python3 build.py
"""
import json
import shutil
from html import escape
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).parent
DIST = ROOT / "docs"  # GitHub Pages מגיש את האתר מהתיקייה docs

WA_ICON = (
    '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>'
)
PLAY_ICON = '<span class="play"><svg viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M6 3.5v13a.7.7 0 001.06.6l10.4-6.5a.7.7 0 000-1.2L7.06 2.9A.7.7 0 006 3.5z"/></svg></span>'


def video_card(video, singer, index):
    """כרטיס סרטון. תומך ב-driveId (גוגל דרייב) או ב-embedUrl + thumb (כל אחסון אחר)."""
    if video.get("driveId"):
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
        f'      <button type="button" class="{classes}" data-src="{escape(src, quote=True)}" '
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

    message = f'היי, ראינו את העמוד של {singer["name"]} ונשמח לשמוע פרטים 🙂'
    phone = "".join(ch for ch in site.get("whatsapp", "") if ch.isdigit())
    wa_href = f"https://wa.me/{phone}?text={quote(message)}"

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
        "waHref": escape(wa_href, quote=True),
        "waIcon": WA_ICON,
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

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(ROOT / "images", DIST / "images")

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

    if not "".join(ch for ch in site.get("whatsapp", "") if ch.isdigit()):
        print("שימו לב: חסר מספר וואטסאפ ב-singers.json (site.whatsapp), הכפתור עדיין לא מוביל אליכם.")


if __name__ == "__main__":
    main()
