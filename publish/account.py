# -*- coding: utf-8 -*-
"""アカウント別のファイル配置。

環境変数 IG_ACCOUNT が空(既定)なら日本語 @mycasestore_net(従来どおりルート直下の
schedule.json / state.json / captions.json)。"en" なら @mycase_en で accounts/en/ 配下。
state.json はアカウントごとに分ける(二重投稿の記録が混ざると壊れる)。
"""
import os

DEFAULT = ""          # 日本語 @mycasestore_net。ファイルはルート直下(移動しない)
KNOWN = {"": "@mycasestore_net", "en": "@mycase_en"}


def name(env=os.environ):
    acc = env.get("IG_ACCOUNT", DEFAULT).strip()
    if acc not in KNOWN:
        raise ValueError(f"未知の IG_ACCOUNT: {acc!r}(使えるのは {sorted(KNOWN)})")
    return acc


def path(filename, account=None, root="."):
    """schedule.json / state.json / captions.json のアカウント別パス"""
    acc = name() if account is None else account
    if acc == DEFAULT:
        return os.path.join(root, filename)
    return os.path.join(root, "accounts", acc, filename)


def release_tag(account=None):
    acc = name() if account is None else account
    return "reels-v1" if acc == DEFAULT else f"reels-{acc}-v1"


def label(account=None):
    acc = name() if account is None else account
    return KNOWN[acc]
