#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""release-assets/manifest.json + captions.json → schedule.json を生成する。

video_url / cover_url は GitHub Releases の公開URL。
  https://github.com/<owner>/<repo>/releases/download/<tag>/<key>.mp4
usage: python3 tools/build_schedule.py [--repo Harapanee/mycase-delivery] [--tag reels-v1]
"""
import datetime
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")


def caption_for(cap, template):
    body = cap["templates"][template]
    return f"{body}\n\n{cap['profile_line']}\n\n{cap['common_tags']}"


def main():
    repo = sys.argv[sys.argv.index("--repo") + 1] if "--repo" in sys.argv else "Harapanee/mycase-delivery"
    tag = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "reels-v1"
    base = f"https://github.com/{repo}/releases/download/{tag}"
    manifest = json.load(open(os.path.join(ROOT, "release-assets", "manifest.json"), encoding="utf-8"))
    cap = json.load(open(os.path.join(ROOT, "captions.json"), encoding="utf-8"))
    items = []
    for m in manifest:
        items.append({
            "key": m["key"],
            "publish_at": m["publish_at"],
            "video_url": f"{base}/{m['key']}.mp4",
            "cover_url": f"{base}/{m['key']}.jpg",
            "caption": caption_for(cap, m["template"]),
            "audio_id": None,
            "audio_title": "動画に焼き込み済み(BGM+SFX)",
            "source": f"mycase-{m['n']}-{m['template']}",
        })
    out = {"generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "items": items}
    with open(os.path.join(ROOT, "schedule.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    lens = [len(i["caption"]) for i in items]
    print(f"{len(items)} 件 / 本文 {min(lens)}〜{max(lens)} 文字(上限2200) / {items[0]['publish_at']} 〜 {items[-1]['publish_at']}")


if __name__ == "__main__":
    main()
