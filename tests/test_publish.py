import sys, os, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "publish"))
from zoneinfo import ZoneInfo
import pytest
import publish as pub
import ig_client

JST = ZoneInfo("Asia/Tokyo")
SCHEDULE = {"items": [
    {"key": "day01_0600", "publish_at": "2026-09-01T06:00:00+09:00",
     "video_url": "v1", "cover_url": "c1", "caption": "本文1", "audio_id": "A1"},
]}
NOW = datetime.datetime(2026, 9, 1, 6, 3, tzinfo=JST)
PREPARED = {"day01_0600": {"status": "prepared", "container_id": "CID1",
                           "container_created_at": "2026-09-01T00:00:00+09:00"}}


class FakeClient:
    ContainerError = ig_client.ContainerError

    def __init__(self, publish_fails=False):
        self.publish_fails = publish_fails
        self.created = []
        self.published = []

    def create_container(self, user_id, token, **kw):
        self.created.append(kw["video_url"])
        return "NEWCID"

    def wait_for_container(self, token, container_id):
        return None

    def publish_container(self, user_id, token, container_id):
        if self.publish_fails:
            raise ig_client.ContainerError("公開失敗")
        self.published.append(container_id)
        return "MEDIA1"


def test_run_準備済みコンテナをそのまま公開する():
    c = FakeClient()
    st, key = pub.run(SCHEDULE, PREPARED, NOW, "IG", "T", client=c)
    assert key == "day01_0600"
    assert c.published == ["CID1"]
    assert c.created == []                       # 作り直していない
    assert st["day01_0600"]["status"] == "published"
    assert st["day01_0600"]["media_id"] == "MEDIA1"


def test_run_公開済みなら何もしない():
    c = FakeClient()
    st, key = pub.run(SCHEDULE, {"day01_0600": {"status": "published"}},
                      NOW, "IG", "T", client=c)
    assert key is None and c.published == []


def test_run_コンテナが無ければ作ってから公開する():
    c = FakeClient()
    st, key = pub.run(SCHEDULE, {}, NOW, "IG", "T", client=c)
    assert c.created == ["v1"]
    assert c.published == ["NEWCID"]
    assert st["day01_0600"]["status"] == "published"


def test_run_コンテナが古ければ作り直す():
    old = {"day01_0600": {"status": "prepared", "container_id": "OLD",
                          "container_created_at": "2026-08-30T00:00:00+09:00"}}
    c = FakeClient()
    st, key = pub.run(SCHEDULE, old, NOW, "IG", "T", client=c)
    assert c.created == ["v1"]
    assert c.published == ["NEWCID"]


def test_run_時刻が範囲外なら何もしない():
    c = FakeClient()
    far = datetime.datetime(2026, 9, 1, 12, 0, tzinfo=JST)  # 判定窓(180分)の外
    st, key = pub.run(SCHEDULE, PREPARED, far, "IG", "T", client=c)
    assert key is None and c.published == []


def test_run_公開に失敗したら例外を送出しstateを更新しない():
    c = FakeClient(publish_fails=True)
    with pytest.raises(ig_client.ContainerError):
        pub.run(SCHEDULE, PREPARED, NOW, "IG", "T", client=c)


def test_main_IG_USER_IDが空なら何もせず正常終了する(tmp_path, monkeypatch):
    """en を追加した直後は Secrets も schedule も無い。publish.yml を落とさないため。"""
    monkeypatch.chdir(tmp_path)
    assert pub.load_schedule_or_skip("schedule.json", "") is None


def test_main_scheduleが無ければ何もせず正常終了する(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert pub.load_schedule_or_skip("accounts/en/schedule.json", "17841000") is None


def test_main_enはaccounts配下のstateに書く(tmp_path, monkeypatch):
    import json, account
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("IG_ACCOUNT", "en")
    monkeypatch.setenv("IG_ACCESS_TOKEN", "T")
    monkeypatch.setenv("IG_USER_ID", "17841000")
    os.makedirs("accounts/en")
    json.dump(SCHEDULE, open("accounts/en/schedule.json", "w"))
    # run() の client= は定義時に束縛されるので、ig_client の関数そのものを差し替える
    fake = FakeClient()
    for fn in ("create_container", "wait_for_container", "publish_container"):
        monkeypatch.setattr(ig_client, fn, getattr(fake, fn))
    monkeypatch.setattr(pub.datetime, "datetime", type("D", (datetime.datetime,), {
        "now": classmethod(lambda cls, tz=None: NOW)}))
    pub.main()
    st = json.load(open("accounts/en/state.json"))
    assert st["day01_0600"]["status"] == "published"
    assert not os.path.exists("state.json"), "日本語側の state.json に書いてはいけない"
