#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完成済みの縦動画 (H.264 1080x1920) を既存の投稿予定の末尾に足す。

stage_assets.py / stage_en_shorts.py + build_schedule.py は schedule.json を作り直すが、
こちらは既存の items を残したまま追記する(公開済みの記録を消さない)。
  ・投稿番号は既存の最大番号の次から、枠はアカウントの定型枠のうち --from 以降
    (--slots 18 のように時を指定すると、その枠だけを使う。型比較で 1 日 1 本・同時刻にそろえるとき用)
  ・動画は再エンコードせず faststart で詰め直す。サムネイルは指定秒のコマ
  ・release-assets/<tag>/ に <key>.mp4 / .jpg を置く → gh release create <tag> で公開
usage: python3 tools/append_batch.py --account ja|en --tag reels-v2 --from 2026-09-23T18:00 [--slots 18] \
         <動画.mp4>:<テンプレート>:<サムネ秒> ...
"""
import datetime
import json
import os
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "publish"))
sys.path.insert(0, os.path.dirname(__file__))
import account  # noqa: E402
from build_schedule import caption_for  # noqa: E402

SLOT_HOURS = {"": [6, 12, 18], "en": [8, 22, 25]}  # 25 = 翌日 01:00(stage_en_shorts.py と同じ)


def slots(acc, first, hours=None):
    day = first.replace(hour=0, minute=0) - datetime.timedelta(days=1)
    while True:
        for h in hours or SLOT_HOURS[acc]:
            at = day + datetime.timedelta(hours=h)
            if at >= first:
                yield at
        day += datetime.timedelta(days=1)


def main():
    a = sys.argv[1:]
    acc = {"ja": "", "en": "en"}[a[a.index("--account") + 1]]
    tag = a[a.index("--tag") + 1]
    first = datetime.datetime.strptime(a[a.index("--from") + 1], "%Y-%m-%dT%H:%M")
    hours = [int(h) for h in a[a.index("--slots") + 1].split(",")] if "--slots" in a else None
    if hours and not set(hours) <= set(SLOT_HOURS[acc]):
        sys.exit(f"--slots は定期実行の枠 {SLOT_HOURS[acc]} の中から選ぶ(それ以外の時刻は発火しない)")
    if first <= datetime.datetime.now() + datetime.timedelta(hours=1):
        sys.exit("--from は 1 時間以上先にする(事前のコンテナ作成が間に合わない)")
    specs = [x for i, x in enumerate(a) if ":" in x and not a[i - 1].startswith("--")]
    sched_path = account.path("schedule.json", acc, ROOT)
    sched = json.load(open(sched_path, encoding="utf-8"))
    cap = json.load(open(account.path("captions.json", acc, ROOT), encoding="utf-8"))
    n0 = max(int(i["key"][:3]) for i in sched["items"])
    known = {i["key"] for i in sched["items"]}
    out = os.path.join(ROOT, "release-assets", tag)
    os.makedirs(out, exist_ok=True)
    base = f"https://github.com/Harapanee/mycase-delivery/releases/download/{tag}"
    for k, (spec, at) in enumerate(zip(specs, slots(acc, first, hours))):
        src, tpl, cover = spec.rsplit(":", 2)
        if tpl not in cap["templates"]:
            sys.exit(f"captions にテンプレート {tpl} が無い")
        key = f"{n0 + k + 1:03d}_{at:%Y%m%d_%H%M}"
        assert key not in known
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-c", "copy", "-movflags", "+faststart",
                        os.path.join(out, key + ".mp4")], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", cover, "-i", src, "-frames:v", "1", "-q:v", "2",
                        os.path.join(out, key + ".jpg")], check=True)
        item = {"key": key, "publish_at": at.strftime("%Y-%m-%dT%H:%M:%S+09:00"),
                "video_url": f"{base}/{key}.mp4", "cover_url": f"{base}/{key}.jpg",
                "caption": caption_for(cap, tpl), "audio_id": None,
                "audio_title": "動画に焼き込み済み(BGM+SFX)", "source": os.path.basename(src)}
        if acc:
            item["account"] = account.label(acc)
        sched["items"].append(item)
        print(key, "←", os.path.basename(src), tpl, f"本文 {len(item['caption'])} 文字")
    sched["generated_at"] = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    with open(sched_path, "w", encoding="utf-8") as f:
        json.dump(sched, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
