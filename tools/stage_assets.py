#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""制作側(MyCase/videos/mycase-zoomout)の31本を、投稿順のファイル名で release-assets/ に並べる。

  NNN_YYYYMMDD_HHMM.mp4  … 動画(コピー)
  NNN_YYYYMMDD_HHMM.jpg  … サムネイル(停止+1.5秒 = ケースに絵が載った瞬間)
  manifest.json          … 元番号・テンプレート・投稿時刻の対応表(schedule.json の材料)

投稿枠は 06:00 / 12:00 / 18:00 JST。開始日は引数(既定 2026-09-13)。
usage: python3 tools/stage_assets.py [YYYY-MM-DD] [--account en --src <英語版レンダーの制作ディレクトリ>]
  --account en なら release-assets/en/ に並べる(manifest.json も同じ場所)。
  --src は制作側ディレクトリ(batch/picks.json と renders/batch/mycase-<n>-<tpl>.mp4 がある場所)。
"""
import datetime
import json
import os
import shutil
import subprocess
import sys

SRC = "/Users/harakoudai/Desktop/ClaudeCode/MyCase/videos/mycase-zoomout"
OUT = os.path.join(os.path.dirname(__file__), "..", "release-assets")
TPL = ["classic", "specs", "qa", "day", "loop", "split", "myth"]
SLOTS = [6, 12, 18]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    acc = sys.argv[sys.argv.index("--account") + 1] if "--account" in sys.argv else ""
    src = sys.argv[sys.argv.index("--src") + 1] if "--src" in sys.argv else SRC
    out = os.path.join(OUT, acc) if acc else OUT
    start = datetime.datetime.strptime(args[0] if args else "2026-09-13", "%Y-%m-%d")
    os.makedirs(out, exist_ok=True)
    picks = json.load(open(os.path.join(src, "batch", "picks.json")))
    rows = []
    for i, k in enumerate(sorted(picks, key=int)):
        n = int(k)
        t = TPL[(n - 1) % 7]
        fz = round(round(picks[k]["freeze"] * 30) / 30, 4)
        at = start.replace(hour=SLOTS[i % 3]) + datetime.timedelta(days=i // 3)
        key = f"{i + 1:03d}_{at:%Y%m%d_%H%M}"
        mp4 = os.path.join(src, "renders", "batch", f"mycase-{n}-{t}.mp4")
        dst = os.path.join(out, key + ".mp4")
        if not os.path.exists(dst):
            shutil.copyfile(mp4, dst)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{fz + 1.5:.3f}", "-i", mp4,
                        "-frames:v", "1", "-q:v", "2", os.path.join(out, key + ".jpg")], check=True)
        rows.append({"key": key, "n": n, "template": t,
                     "publish_at": at.strftime("%Y-%m-%dT%H:%M:%S+09:00"),
                     "src": os.path.relpath(mp4, src)})
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print(len(rows), rows[0]["key"], "→", rows[-1]["key"])


if __name__ == "__main__":
    main()
