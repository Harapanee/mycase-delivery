import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "publish"))
import pytest
import account


def test_既定は日本語でルート直下():
    assert account.name({}) == ""
    assert account.path("state.json", "") == "./state.json"
    assert account.release_tag("") == "reels-v1"
    assert account.label("") == "@mycasestore_net"


def test_enはaccounts配下で別state():
    assert account.name({"IG_ACCOUNT": "en"}) == "en"
    assert account.path("state.json", "en") == "./accounts/en/state.json"
    assert account.path("schedule.json", "en") == "./accounts/en/schedule.json"
    assert account.release_tag("en") == "reels-en-v1"
    assert account.label("en") == "@mycase_en"


def test_未知のアカウントは拒否する():
    """typo で日本語の state.json に英語の投稿記録を混ぜないため"""
    with pytest.raises(ValueError):
        account.name({"IG_ACCOUNT": "eng"})
