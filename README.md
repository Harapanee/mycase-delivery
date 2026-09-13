# mycase-delivery

Instagram **@mycasestore_net**(MyCase 公式)のリールを自動投稿する配信リポジトリ。
`yuuto-career-delivery` の骨組みをそのまま流用している(投稿スクリプトは同一、枠だけ1日3本)。

制作は `MyCase/videos/mycase-zoomout/`(private)。ここに置くのは **投稿予定・投稿済み記録・投稿スクリプト**だけ。動画は Releases に置く。

```
[private] MyCase/videos/mycase-zoomout      [public] このリポジトリ
  renders/batch/mycase-<n>-<template>.mp4 →   tools/stage_assets.py → release-assets/(gitignore)
                                              tools/build_schedule.py → schedule.json  投稿予定
                                              GitHub Actions(cron) + publish/           投稿
                                              state.json                                投稿済み記録
                                              Releases reels-v1                         動画とサムネイル
```

## 投稿スロット
**1日3本(06:00 / 12:00 / 18:00 JST)**。31本 = 2026-09-13 06:00 〜 2026-09-23 06:00。

| ジョブ | cron (UTC) | JST | 役割 |
|---|---|---|---|
| prepare | `0 15 * * *` | 00:00 | その日の3本のコンテナを事前作成。**前倒し禁止**(日付が前日になる) |
| prepare | `50 20 * * *` | 05:50 | 0時が発火しなかった場合の保険 |
| publish | `41,48,56 20` / `3 21` | 05:41〜06:03 | 06:00 の回(4発) |
| publish | `41,48,56 2` / `3 3` | 11:41〜12:03 | 12:00 の回(4発) |
| publish | `41,48,56 8` / `3 9` | 17:41〜18:03 | 18:00 の回(4発) |

cron を1枠4発置いてあるのは GitHub の定時実行が遅延・欠落するため。publish.py は「公開済みならスキップ」「予定時刻の −35分〜+180分の外ならスキップ」なので何発撃っても二重投稿にならない。**cron が無い時刻は schedule.json に書いても永久に投稿されない。**

## 安全装置
| 項目 | 実装 |
|---|---|
| 二重投稿の防止 | `state.json` による冪等性。投稿は取り消せない |
| 記録の破損防止 | tmp + `os.replace` のアトミック書き込み |
| 取りこぼしの暴発防止 | 判定窓の外では何もしない(取りこぼしは `workflow_dispatch` の key 指定で手動公開) |
| 失敗を成功と記録しない | 公開が成功したあとにだけ記録を更新 |
| secrets の漏洩防止 | **`pull_request` トリガーを付けない**(public) |

## Secrets
| 名前 | 中身 |
|---|---|
| `IG_ACCESS_TOKEN` | Meta ビジネスポートフォリオ `MyCase`(667986306034264)のシステムユーザー `bizbot` のトークン。`EAA...` で始まること |
| `IG_USER_ID` | MyCase 公式 Instagram の IG ユーザーID(17841... の形式) |

トークンは60日で失効する。healthcheck が毎朝残日数を出し、14日を切ると警告する。更新手順は `../ゆうとキャリア/HANDOFF.md` 冒頭(同じシステムユーザー)。

## 発火の仕組み(2026-09-13 変更)
GitHub の `schedule` は公開直後のリポジトリで最大5時間遅れ、9/13 の 12:00/18:00 枠が窓の外で全スキップされた。
そのため発火は Claude のクラウド定期実行 `trig_01Q1Rfj3Z72yb8KkPS7VfsGD`(毎日 05:55/11:55/17:55 JST)が担う。
定期実行は `trigger/fire.txt` に1行追記して push するだけで、publish.yml は `push: paths: trigger/**` で即時発火する(試運転: 起動→push 19秒→発火 12秒)。
`schedule` の4発は保険として残してある。投稿の判断(時刻窓・公開済みスキップ)は従来どおり publish.py が行うので、二重投稿にはならない。
定期実行の管理: https://claude.ai/code/routines/trig_01Q1Rfj3Z72yb8KkPS7VfsGD

## 素材の更新手順
```bash
python3 tools/stage_assets.py 2026-09-13     # 制作側の31本を投稿順にリネーム+サムネイル
python3 tools/build_schedule.py              # captions.json と合わせて schedule.json を生成
gh release create reels-v1 release-assets/*.mp4 release-assets/*.jpg --title "reels v1" --notes "31本"
python3 -m pytest tests -q
```

## 本番投入の前に必ずやること
1. Secrets を入れたら **疎通確認ワークフロー(healthcheck.yml)を手動実行**して `content_publishing_limit` が返るのを見る
2. **1本だけ**で通しを確認する(全件投入しない)
3. **同じ実行を2回叩いて二重投稿しないことを確認する**
4. 投稿後、実際にアプリで音・サムネイル・本文を見る

## テスト
```bash
python3 -m pytest tests -q
```
