#!/usr/bin/env python3
"""Teams トランスクリプト(.vtt) を取得し、「70_議事録 運用ルール」に従って格納する。

処理の流れ
  1. Microsoft Graph にサインイン(デバイスコード認証・委任権限)
  2. 期間内のカレンダー予定(Teams会議)から会議名キーワードに合うものを抽出
  3. 各回のトランスクリプトを .vtt でダウンロード
  4. 運用ルールの命名規約・フォルダ構成に変換(UTC -> JST)
  5. 格納先(ローカル/共有フォルダ, OneDrive, SharePoint)へアップロード

使い方の例は README_transcript_sync.md を参照。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, urlparse
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
UTC = dt.timezone.utc
GRAPH = "https://graph.microsoft.com/v1.0"
SCOPES = [
    "Calendars.Read",
    "OnlineMeetings.Read",
    "OnlineMeetingTranscript.Read.All",
    "Files.ReadWrite.All",  # OneDrive / SharePoint へ書く場合のみ使用
]
WEEKDAY_KANJI = "月火水木金土日"
WEEKLY_NAME = "中国TSUチーム定例会"


# ----------------------------------------------------------------------------
# 運用ルール(命名・フォルダ構成)  ※ 純粋関数。通信なしでテスト可能
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class Placement:
    kind: str  # "weekly" | "daily"
    rel_dir: str  # ルート(70_議事録)からの相対フォルダ(/区切り)
    filename: str
    extra_dirs: tuple[str, ...]  # 併せて作る空フォルダ(10_議事録 など)


def classify(start_jst: dt.datetime) -> str:
    """月曜=週次定例、火〜金=Daily。それ以外は対象外。"""
    wd = start_jst.weekday()
    if wd == 0:
        return "weekly"
    if 1 <= wd <= 4:
        return "daily"
    raise ValueError(f"対象外の曜日です: {start_jst:%Y-%m-%d}({WEEKDAY_KANJI[wd]})")


def place(start_jst: dt.datetime, seq: int = 1) -> Placement:
    """開催日時(JST)から格納先とファイル名を決める。seq>1 は同日2本目以降。"""
    if start_jst.tzinfo is None or start_jst.utcoffset() != dt.timedelta(hours=9):
        raise ValueError("start_jst は JST(+09:00) の aware datetime で渡してください")
    ymd = f"{start_jst:%Y%m%d}"
    suffix = "" if seq == 1 else f"_{seq}"
    kind = classify(start_jst)
    if kind == "weekly":
        half = "前半" if start_jst.hour < 15 else "後半"  # 月13:00=前半 / 17:00=後半
        base = f"{start_jst.year}/01_週次定例/{ymd}_{WEEKLY_NAME}"
        return Placement(
            kind,
            f"{base}/00_transcript",
            f"{ymd}_{start_jst:%H%M}_{half}{suffix}.vtt",
            (f"{base}/10_議事録", f"{base}/20_資料"),
        )
    iso_year, iso_week, _ = start_jst.isocalendar()
    wk = f"{iso_year}-W{iso_week:02d}"
    base = f"{iso_year}/02_Daily/{wk}"  # 年またぎ週はISO年に寄せる
    day = WEEKDAY_KANJI[start_jst.weekday()]
    return Placement(
        kind,
        f"{base}/00_transcript",
        f"{ymd}_{day}{suffix}.vtt",
        (f"{base}/10_ログ",),
    )


# ----------------------------------------------------------------------------
# Graph クライアント
# ----------------------------------------------------------------------------
class Graph:
    def __init__(self, token: str):
        import requests

        self.s = requests.Session()
        self.s.headers["Authorization"] = f"Bearer {token}"

    def get(self, url, **kw):
        r = self.s.get(url if url.startswith("http") else GRAPH + url, **kw)
        r.raise_for_status()
        return r

    def pages(self, url, **kw):
        while url:
            j = self.get(url, **kw).json()
            yield from j.get("value", [])
            url, kw = j.get("@odata.nextLink"), {}


def sign_in(client_id: str, tenant: str) -> str:
    import msal

    cache_path = Path.home() / ".cache" / "teams_transcript_sync" / "token.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache = msal.SerializableTokenCache()
    if cache_path.exists():
        cache.deserialize(cache_path.read_text())
    app = msal.PublicClientApplication(
        client_id, authority=f"https://login.microsoftonline.com/{tenant}", token_cache=cache
    )
    res = None
    accts = app.get_accounts()
    if accts:
        res = app.acquire_token_silent(SCOPES, account=accts[0])
    if not res:
        flow = app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            sys.exit(f"デバイスコード認証を開始できません: {flow}")
        print(flow["message"], file=sys.stderr)
        res = app.acquire_token_by_device_flow(flow)
    if "access_token" not in res:
        sys.exit(f"サインイン失敗: {res.get('error_description', res)}")
    cache_path.write_text(cache.serialize())
    os.chmod(cache_path, 0o600)
    return res["access_token"]


@dataclass
class Occurrence:
    subject: str
    start: dt.datetime  # JST
    end: dt.datetime  # JST
    join_url: str


def find_occurrences(g: Graph, since: dt.date, until: dt.date, keyword: str) -> list[Occurrence]:
    params = {
        "startDateTime": f"{since:%Y-%m-%d}T00:00:00",
        "endDateTime": f"{until + dt.timedelta(days=1):%Y-%m-%d}T00:00:00",
        "$select": "subject,start,end,isOnlineMeeting,onlineMeeting,isCancelled",
        "$top": "100",
    }
    hdr = {"Prefer": 'outlook.timezone="Asia/Tokyo"'}  # 返却時刻をJSTにする
    out = []
    for ev in g.pages("/me/calendarView", params=params, headers=hdr):
        if ev.get("isCancelled") or not ev.get("isOnlineMeeting"):
            continue
        if keyword not in (ev.get("subject") or ""):
            continue
        url = (ev.get("onlineMeeting") or {}).get("joinUrl")
        if not url:
            continue
        parse = lambda d: dt.datetime.fromisoformat(d["dateTime"][:19]).replace(tzinfo=JST)
        out.append(Occurrence(ev["subject"], parse(ev["start"]), parse(ev["end"]), url))
    return sorted(out, key=lambda o: o.start)


def fetch_transcripts(g: Graph, occ: Occurrence, meeting_cache: dict) -> list[tuple[str, bytes]]:
    """この回に該当するトランスクリプトを [(id, vtt bytes)] で返す。
    繰り返し会議は全回が同じ joinUrl なので、作成時刻で回を突き合わせる。"""
    if occ.join_url not in meeting_cache:
        q = {"$filter": f"JoinWebUrl eq '{occ.join_url}'"}
        vals = g.get("/me/onlineMeetings", params=q).json().get("value", [])
        meeting_cache[occ.join_url] = vals[0]["id"] if vals else None
    mid = meeting_cache[occ.join_url]
    if not mid:
        return []
    lo, hi = occ.start - dt.timedelta(minutes=30), occ.end + dt.timedelta(hours=2)
    res = []
    for t in g.pages(f"/me/onlineMeetings/{mid}/transcripts"):
        created = dt.datetime.fromisoformat(t["createdDateTime"].replace("Z", "+00:00")).astimezone(JST)
        if lo <= created <= hi:
            body = g.get(
                f"/me/onlineMeetings/{mid}/transcripts/{t['id']}/content", params={"$format": "text/vtt"}
            ).content
            res.append((created.isoformat(), body))
    res.sort()
    return res


# ----------------------------------------------------------------------------
# アップロード先
# ----------------------------------------------------------------------------
class LocalDest:
    def __init__(self, root: str):
        self.root = Path(root)

    def put(self, rel: str, data: bytes, overwrite: bool) -> str:
        p = self.root / rel
        if p.exists() and not overwrite:
            return "skip"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return "put"

    def mkdir(self, rel: str):
        (self.root / rel).mkdir(parents=True, exist_ok=True)


class DriveDest:
    """OneDrive(/me/drive) または SharePoint ドキュメントライブラリ(/drives/{id})。"""

    def __init__(self, g: Graph, drive_base: str, root_path: str):
        self.g, self.base, self.root = g, drive_base, root_path.strip("/")

    def _p(self, rel: str) -> str:
        full = f"{self.root}/{rel}" if self.root else rel
        return quote(full.strip("/"), safe="/")

    def put(self, rel: str, data: bytes, overwrite: bool) -> str:
        cb = "replace" if overwrite else "fail"
        r = self.g.s.put(
            f"{GRAPH}{self.base}/root:/{self._p(rel)}:/content?@microsoft.graph.conflictBehavior={cb}",
            data=data,
            headers={"Content-Type": "text/vtt"},
        )
        if r.status_code == 409 and not overwrite:
            return "skip"
        r.raise_for_status()  # 本ファイルは小さい(4MB未満)ので単純PUTで足りる
        return "put"

    def mkdir(self, rel: str):
        parent = ""
        for seg in (self.root + "/" + rel).strip("/").split("/"):
            url = (
                f"{GRAPH}{self.base}/root:/{quote(parent, safe='/')}:/children"
                if parent
                else f"{GRAPH}{self.base}/root/children"
            )
            r = self.g.s.post(
                url, json={"name": seg, "folder": {}, "@microsoft.graph.conflictBehavior": "fail"}
            )
            if r.status_code not in (200, 201, 409):
                r.raise_for_status()
            parent = f"{parent}/{seg}".strip("/")


def sharepoint_drive_base(g: Graph, site_url: str, library: str | None) -> str:
    u = urlparse(site_url)
    site = g.get(f"/sites/{u.hostname}:{u.path.rstrip('/')}").json()
    if not library:
        return f"/sites/{site['id']}/drive"
    for d in g.pages(f"/sites/{site['id']}/drives"):
        if d["name"] == library:
            return f"/drives/{d['id']}"
    sys.exit(f"ドキュメントライブラリ '{library}' が見つかりません")


# ----------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", required=True, type=dt.date.fromisoformat, help="対象期間の開始日(JST) YYYY-MM-DD")
    ap.add_argument("--until", type=dt.date.fromisoformat, default=dt.datetime.now(JST).date(), help="終了日(既定:今日)")
    ap.add_argument("--keyword", default="中国TSU", help="会議名に含まれる文字列(既定: 中国TSU)")
    ap.add_argument("--dest", required=True, choices=["local", "onedrive", "sharepoint"])
    ap.add_argument("--root", default="70_議事録", help="local: 70_議事録 フォルダのパス / onedrive,sharepoint: ライブラリ内の相対パス")
    ap.add_argument("--site-url", help="sharepoint: サイトURL 例 https://xxx.sharepoint.com/sites/yyy")
    ap.add_argument("--library", help="sharepoint: ドキュメントライブラリ名(省略時は既定ライブラリ)")
    ap.add_argument("--overwrite", action="store_true", help="既存ファイルを上書き(既定はスキップ)")
    ap.add_argument("--dry-run", action="store_true", help="ダウンロード/アップロードせず格納先だけ表示")
    ap.add_argument("--client-id", default=os.environ.get("TTS_CLIENT_ID"), help="Entra ID アプリの Client ID (env: TTS_CLIENT_ID)")
    ap.add_argument("--tenant", default=os.environ.get("TTS_TENANT_ID", "organizations"), help="テナントID (env: TTS_TENANT_ID)")
    a = ap.parse_args(argv)
    if not a.client_id:
        sys.exit("--client-id か環境変数 TTS_CLIENT_ID が必要です")
    if a.dest == "sharepoint" and not a.site_url:
        sys.exit("--dest sharepoint には --site-url が必要です")

    g = Graph(sign_in(a.client_id, a.tenant))
    if a.dest == "local":
        dest = LocalDest(a.root)
    elif a.dest == "onedrive":
        dest = DriveDest(g, "/me/drive", a.root)
    else:
        dest = DriveDest(g, sharepoint_drive_base(g, a.site_url, a.library), a.root)

    occs = find_occurrences(g, a.since, a.until, a.keyword)
    print(f"対象の会議: {len(occs)}件", file=sys.stderr)
    cache, used, summary = {}, {}, []
    for o in occs:
        try:
            transcripts = None if a.dry_run else fetch_transcripts(g, o, cache)
        except Exception as e:  # 1件の失敗で全体を止めない
            print(f"! {o.start:%F %R} {o.subject}: 取得失敗 {e}", file=sys.stderr)
            continue
        n = 1 if transcripts is None else len(transcripts)
        if n == 0:
            print(f"- {o.start:%F %R} {o.subject}: トランスクリプトなし(文字起こしOFF?)", file=sys.stderr)
            continue
        for i in range(n):
            seq = used[(o.start.date(), o.start.hour // 15)] = used.get((o.start.date(), o.start.hour // 15), 0) + 1
            try:
                pl = place(o.start, seq)
            except ValueError as e:
                print(f"- スキップ: {e}", file=sys.stderr)
                continue
            rel = f"{pl.rel_dir}/{pl.filename}"
            if a.dry_run:
                print(f"[dry-run] {o.start:%F %R} -> {rel}")
                continue
            for d in pl.extra_dirs:
                dest.mkdir(d)
            status = dest.put(rel, transcripts[i][1], a.overwrite)
            print(f"[{status}] {rel}")
            summary.append({"status": status, "path": rel, "subject": o.subject})
    if not a.dry_run:
        print(json.dumps(summary, ensure_ascii=False, indent=1), file=sys.stderr)


if __name__ == "__main__":
    main()
