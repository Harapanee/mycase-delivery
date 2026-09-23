#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公開済みリールのインサイト(再生・リーチ・保存・シェア・平均視聴秒数など)を 1 本 1 行の CSV にする。

動画の型ごとの伸び方を比べるためのもの。型は schedule.json の source(ファイル名)から付ける。
トークンに instagram_manage_insights が要る(無いと code 10 / 200 で落ちる)。
トークンは環境変数 IG_ACCESS_TOKEN、無ければ ~/.mycase_ig_token。値は表示しない。
usage: python3 tools/reel_insights.py [--account ja|en] [--out insights.csv]
"""
import csv
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "publish"))
import account  # noqa: E402

BASE = "https://graph.facebook.com/v22.0"
METRICS = ["views", "reach", "saved", "shares", "likes", "comments", "total_interactions",
           "ig_reels_avg_watch_time", "ig_reels_video_view_total_time"]


def get(path, token, **params):
    params["access_token"] = token
    url = f"{BASE}/{path}?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        err = json.loads(e.read().decode()).get("error", {})
        raise SystemExit(f"API エラー {err.get('code')}: {err.get('message')}"
                         + ("\n→ トークンに instagram_manage_insights が無い可能性" if err.get("code") in (10, 200) else ""))


def kind(source):
    """ファイル名から動画の型を取り出す(例 s2-03-quiz.mp4 → s2-quiz / mycase-9-specs → specs)"""
    s = os.path.splitext(source or "")[0]
    m = re.match(r"(s\d+)-\d+-([a-z]+)", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    m = re.match(r"(v\d-[a-z]+)", s)
    if m:
        return "dopa-" + m.group(1)
    if s == "mycase-dopa-ad":
        return "dopa-v1-dopa"
    return s.split("-")[-1] or "?"


def main():
    a = sys.argv[1:]
    acc = {"ja": "", "en": "en"}[a[a.index("--account") + 1]] if "--account" in a else ""
    out = a[a.index("--out") + 1] if "--out" in a else None
    token = os.environ.get("IG_ACCESS_TOKEN") or open(os.path.expanduser("~/.mycase_ig_token")).read().strip()
    sched = {i["key"]: i for i in json.load(open(account.path("schedule.json", acc, ROOT), encoding="utf-8"))["items"]}
    state = json.load(open(account.path("state.json", acc, ROOT), encoding="utf-8"))
    rows = []
    for key, st in sorted(state.items()):
        if st.get("status") != "published" or not st.get("media_id"):
            continue
        res = get(f"{st['media_id']}/insights", token, metric=",".join(METRICS))
        vals = {d["name"]: d["values"][0]["value"] for d in res.get("data", [])}
        src = sched.get(key, {}).get("source", "")
        row = {"key": key, "kind": kind(src), "source": src, "published_at": st.get("published_at", "")[:16]}
        row.update({m: vals.get(m, "") for m in METRICS})
        if isinstance(row["ig_reels_avg_watch_time"], (int, float)):
            row["ig_reels_avg_watch_time"] = round(row["ig_reels_avg_watch_time"] / 1000, 2)  # ms → 秒
        rows.append(row)
    cols = ["key", "kind", "source", "published_at"] + METRICS
    w = csv.DictWriter(open(out, "w", newline="", encoding="utf-8") if out else sys.stdout, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)


if __name__ == "__main__":
    main()
