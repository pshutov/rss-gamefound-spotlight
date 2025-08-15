#!/usr/bin/env python3

import json, sys, argparse, urllib.request, urllib.error
from datetime import datetime, timezone
from email.utils import format_datetime
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
import os
import mimetypes

API_DEFAULT = "https://gamefound.com/api/platformEvents/getSpotlightPlatformEvents?eventCount=15&olderThanEventId=&excludeDemotedProjects=true"
BASE_URL = "https://gamefound.com"

TYPE_MAP = {
    0: "Launch date",
    1: "Campaign start",
    3: "New project",
    6: "24 hours left",
}

def iso_to_rfc2822(s):
    if s.endswith("Z"):
        s = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return format_datetime(dt.astimezone(timezone.utc))

def guess_mime(url):
    mt, _ = mimetypes.guess_type(url)
    return mt or "image/jpeg"

def build_rss(data, feed_title, feed_link, feed_desc):
    rss = ET.Element("rss", attrib={"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = feed_title
    ET.SubElement(channel, "link").text = feed_link
    ET.SubElement(channel, "description").text = feed_desc
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(datetime.now(timezone.utc))
    ET.SubElement(channel, "ttl").text = "15"

    for it in data:
        title_bits = []
        if it.get("displayTitle"):
            title_bits.append(it["displayTitle"])
        tname = TYPE_MAP.get(it.get("type"))
        if tname:
            title_bits.append(f"[{tname}]")
        title = " ".join(title_bits) or (it.get("displayText") or "Update")

        link = urljoin(BASE_URL, it.get("targetUrl","/"))
        guid = str(it.get("platformEventID") or it.get("projectID") or link)
        pub_date = iso_to_rfc2822(it.get("createdAt"))

        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = link
        g = ET.SubElement(item, "guid", attrib={"isPermaLink": "false"})
        g.text = guid
        ET.SubElement(item, "pubDate").text = pub_date
        
        desc = it.get("displayText") or ""
        ET.SubElement(item, "description").text = desc

        img = it.get("displayImageUrl")
        if img:
            ET.SubElement(item, "enclosure", attrib={"url": img, "type": guess_mime(img)})

    return ET.ElementTree(rss)

def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "rss-maker/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default=API_DEFAULT, help="Gamefound API URL")
    ap.add_argument("--out", default="dist/gamefound_spotlight.xml", help="Output RSS path")
    ap.add_argument("--title", default="Gamefound Spotlight (unofficial)")
    ap.add_argument("--link", default=API_DEFAULT)
    ap.add_argument("--desc", default="RSS feed generated from Gamefound Spotlight API")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    try:
        data = fetch_json(args.api)
    except urllib.error.URLError as e:
        print(f"Failed to fetch API: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, list):
        print("Unexpected API payload (expected list).", file=sys.stderr)
        sys.exit(2)

    tree = build_rss(data, args.title, args.link, args.desc)
    
    ET.indent(tree, space="  ", level=0)  # Python 3.9+
    tree.write(args.out, encoding="utf-8", xml_declaration=True)
    print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()
