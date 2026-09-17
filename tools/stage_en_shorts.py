#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""英語 @mycase_en 用: ユーザーが用意した縦動画フォルダを release-assets/en/ に並べる。

制作側の構造(picks.json)を持たない素材向け。stage_assets.py の en 版。
  ・ファイル名の数字順(1ttp, ttp2, … ttp12)に投稿順を振る
  ・HEVC 4K → H.264 1080x1920 / AAC に変換(Instagram API は 1080 幅の H.264 が推奨)
  ・サムネイルは長さの 75% 地点(ケースに絵が載っている終盤)
  ・manifest.json を書く(build_schedule.py --account en の材料)
usage: python3 tools/stage_en_shorts.py <動画フォルダ> <開始日 YYYY-MM-DD>
"""
import datetime
import json
import os
import re
import subprocess
import sys

OUT = os.path.join(os.path.dirname(__file__), "..", "release-assets", "en")
TPL = ["classic", "specs", "qa", "day", "loop", "split", "myth"]
SLOTS = [6, 12, 18]


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def main():
    src_dir, start = sys.argv[1], datetime.datetime.strptime(sys.argv[2], "%Y-%m-%d")
    os.makedirs(OUT, exist_ok=True)
    files = [f for f in os.listdir(src_dir) if f.lower().endswith(".mp4")]
    files.sort(key=lambda f: int(re.search(r"\d+", f).group()))
    rows = []
    for i, f in enumerate(files):
        n = int(re.search(r"\d+", f).group())
        t = TPL[(n - 1) % 7]
        at = start.replace(hour=SLOTS[i % 3]) + datetime.timedelta(days=i // 3)
        key = f"{i + 1:03d}_{at:%Y%m%d_%H%M}"
        src = os.path.join(src_dir, f)
        dst = os.path.join(OUT, key + ".mp4")
        if not os.path.exists(dst):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src,
                            "-vf", "scale=1080:1920", "-c:v", "libx264", "-preset", "medium",
                            "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
                            "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", dst], check=True)
        d = duration(dst)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{d * 0.75:.3f}", "-i", dst,
                        "-frames:v", "1", "-q:v", "2", os.path.join(OUT, key + ".jpg")], check=True)
        rows.append({"key": key, "n": n, "template": t,
                     "publish_at": at.strftime("%Y-%m-%dT%H:%M:%S+09:00"), "src": f,
                     "duration": round(d, 2)})
        print(key, "←", f, t, f"{d:.1f}s")
    with open(os.path.join(OUT, "manifest.json"), "w", encoding="utf-8") as ff:
        json.dump(rows, ff, ensure_ascii=False, indent=1)
    print(len(rows), rows[0]["key"], "→", rows[-1]["key"])


if __name__ == "__main__":
    main()
