#!/usr/bin/env python3

import json, sys, argparse, re, urllib.request, urllib.error, logging
from datetime import datetime, timezone
from email.utils import format_datetime
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
import os
import mimetypes

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

API_DEFAULT = "https://gamefound.com/api/platformEvents/getSpotlightPlatformEvents?eventCount=15&olderThanEventId=&excludeDemotedProjects=true"
BASE_URL = "https://gamefound.com"

def _parse_iso(s):
    if s.endswith("Z"):
        s = s.replace("Z", "+00:00")
    s = re.sub(r"\.\d+", "", s)  # strip fractional seconds
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def iso_to_rfc2822(s):
    return format_datetime(_parse_iso(s).astimezone(timezone.utc))

def guess_mime(url):
    mt, _ = mimetypes.guess_type(url)
    return mt or "image/jpeg"

def latest_date(data):
    """Return the newest createdAt from items, or current UTC time if none."""
    dates = []
    for it in data:
        raw = it.get("createdAt")
        if raw:
            dates.append(_parse_iso(raw))
    return max(dates) if dates else datetime.now(timezone.utc)

def build_rss(data, feed_title, feed_link, feed_desc):
    rss = ET.Element("rss", attrib={"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = feed_title
    ET.SubElement(channel, "link").text = feed_link
    ET.SubElement(channel, "description").text = feed_desc
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(latest_date(data))
    ET.SubElement(channel, "ttl").text = "15"

    for it in data:
        typ = (it.get("displayTitle") or "").strip()
        name = (it.get("displayText") or "").strip()

        title = f"[{typ}] {name}".strip() if (typ or name) else "Update"
        desc = typ or ""

        link = urljoin(BASE_URL, it.get("targetUrl","/"))
        guid = str(it.get("platformEventID") or it.get("projectID") or link)
        pub_date = iso_to_rfc2822(it.get("createdAt"))

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = link
        g = ET.SubElement(item, "guid", attrib={"isPermaLink": "false"})
        g.text = guid
        ET.SubElement(item, "pubDate").text = pub_date
        ET.SubElement(item, "description").text = desc

        img = it.get("displayImageUrl")
        if img:
            ET.SubElement(item, "enclosure", attrib={"url": img, "type": guess_mime(img)})

    return ET.ElementTree(rss)

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

def _fetch_urllib(url):
    log.info("Trying urllib (direct request)")
    req = urllib.request.Request(url, headers=BROWSER_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def _fetch_cloudscraper(url):
    log.info("Trying cloudscraper")
    import cloudscraper
    scraper = cloudscraper.create_scraper()
    resp = scraper.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()

def _fetch_curl_cffi(url):
    log.info("Trying curl_cffi")
    from curl_cffi import requests as cffi_requests
    resp = cffi_requests.get(url, impersonate="chrome", timeout=30)
    resp.raise_for_status()
    return resp.json()

def fetch_json(url):
    for name, fn in [("urllib", _fetch_urllib), ("cloudscraper", _fetch_cloudscraper), ("curl_cffi", _fetch_curl_cffi)]:
        try:
            data = fn(url)
            log.info("Fetched successfully via %s", name)
            return data
        except Exception as e:
            log.warning("Failed via %s: %s", name, e)
    raise RuntimeError("All fetch methods failed")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default=API_DEFAULT, help="Gamefound API URL")
    ap.add_argument("--out", default="dist/gamefound_spotlight.xml", help="Output RSS path")
    ap.add_argument("--title", default="Gamefound Spotlight (unofficial)")
    ap.add_argument("--link", default=API_DEFAULT)
    ap.add_argument("--desc", default="RSS feed generated from Gamefound Spotlight API")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    log.info("Fetching API: %s", args.api)
    try:
        data = fetch_json(args.api)
    except Exception as e:
        log.error("Failed to fetch API: %s", e)
        sys.exit(1)

    if not isinstance(data, list):
        log.error("Unexpected API payload (expected list), got %s", type(data).__name__)
        sys.exit(2)

    log.info("Received %d items from API", len(data))
    tree = build_rss(data, args.title, args.link, args.desc)

    ET.indent(tree, space="  ", level=0)  # Python 3.9+
    tree.write(args.out, encoding="utf-8", xml_declaration=True)
    log.info("Wrote %s", args.out)

if __name__ == "__main__":
    main()
