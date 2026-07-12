# -*- coding: utf-8 -*-
"""
爬取歌手信息（网易云音乐）

数据来源接口（未加密的老接口，很多爬虫教程都用这套）：
- 歌手分类列表: https://music.163.com/api/artist/list?type=-1&area=-1&initial=-1&limit=...&offset=...
- 歌手详情:     https://music.163.com/api/artist/{id}

产出文件：
- crawler/data/singers.jsonl        每行一个歌手的原始信息（不含爬到的歌曲id，歌曲爬虫会单独关联）
- crawler/data/images/singer_{id}.jpg

用法：
    python crawl_singers.py --target 120
（先爬 120 个歌手，比要求的 100 多留一些余量，防止个别歌手没有可用歌曲导致数量不够）
"""
import argparse
import time

from utils import (
    get_json,
    download_image,
    polite_sleep,
    load_checkpoint,
    save_checkpoint,
    append_jsonl,
    read_jsonl,
)

ARTIST_LIST_URL = "https://music.163.com/api/artist/list"
ARTIST_DETAIL_URL = "https://music.163.com/api/artist/{id}"


def fetch_singer_ids(target_count):
    """分页拉取歌手列表，直到凑够 target_count 个不同歌手 id。"""
    ids = []
    offset = 0
    limit = 30
    # type=-1 表示不限类型（华语/欧美/日本/韩国等都会覆盖到），area=-1 不限地区
    while len(ids) < target_count and offset < 1000:
        data = get_json(
            ARTIST_LIST_URL,
            params={"type": -1, "area": -1, "initial": -1, "limit": limit, "offset": offset},
        )
        polite_sleep()
        if not data or "artists" not in data or not data["artists"]:
            print("歌手列表接口没有更多数据了，提前结束分页。")
            break
        for artist in data["artists"]:
            aid = artist.get("id")
            if aid and aid not in ids:
                ids.append(aid)
        offset += limit
        print(f"已收集歌手 id: {len(ids)} / {target_count}")
    return ids[:target_count]


def fetch_singer_detail(singer_id):
    data = get_json(ARTIST_DETAIL_URL.format(id=singer_id))
    if not data or "artist" not in data:
        return None
    artist = data["artist"]
    hot_songs = data.get("hotSongs", [])
    record = {
        "singer_id": singer_id,
        "name": artist.get("name", ""),
        "img_url_raw": artist.get("picUrl") or artist.get("img1v1Url", ""),
        "bio": (artist.get("briefDesc") or "暂无歌手简介").strip(),
        "source_url": f"https://music.163.com/#/artist?id={singer_id}",
        "hot_song_ids": [s.get("id") for s in hot_songs if s.get("id")],
    }
    return record


def main(target):
    ckpt = load_checkpoint()
    done_ids = set(ckpt.get("singer_ids_done", []))
    existing = {r["singer_id"] for r in read_jsonl("singers.jsonl")}
    done_ids |= existing

    singer_ids = fetch_singer_ids(target + 20)  # 多拉一些，防止详情接口失败导致数量不够

    for sid in singer_ids:
        if len([x for x in done_ids]) >= target:
            break
        if sid in done_ids:
            continue
        detail = fetch_singer_detail(sid)
        polite_sleep()
        if not detail:
            print(f"[跳过] 歌手 {sid} 详情获取失败")
            continue
        local_img = download_image(detail["img_url_raw"], f"singer_{sid}.jpg")
        detail["local_image"] = local_img
        append_jsonl("singers.jsonl", detail)
        done_ids.add(sid)
        ckpt["singer_ids_done"] = list(done_ids)
        save_checkpoint(ckpt)
        print(f"[完成] 歌手《{detail['name']}》 ({len(done_ids)}/{target})")

    print(f"歌手爬取结束，共获得 {len(done_ids)} 位歌手，数据在 crawler/data/singers.jsonl")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=120, help="目标歌手数量")
    args = parser.parse_args()
    main(args.target)
