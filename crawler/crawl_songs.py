# -*- coding: utf-8 -*-
"""
爬取歌曲信息（网易云音乐）

依赖 crawl_singers.py 先跑完，产出 data/singers.jsonl（每个歌手带 hot_song_ids）。
对每个歌手：
  1. 用歌手页热门歌曲 id（hot_song_ids）打底
  2. 再用 /api/artist/{id}/desc 或歌手全部歌曲接口补充，凑够每个歌手至少 1 首、
     总数不少于 2000 首（可以通过 --per-singer 调整每个歌手爬取的歌曲数量上限）

接口：
- 歌曲详情（可批量）: https://music.163.com/api/song/detail?ids=[id1,id2,...]
- 歌词:               https://music.163.com/api/song/lyric?id={id}&lv=1&kv=1&tv=-1
- 歌手全部歌曲:        https://music.163.com/api/v1/artist/songs?id={id}&order=hot&limit=100&offset=0

产出：
- crawler/data/songs.jsonl
- crawler/data/images/song_{id}.jpg

注意：只保留【有歌词】的歌曲（作业要求歌曲详情页必须展示歌词）。
"""
import argparse
import re

from utils import (
    get_json,
    download_image,
    polite_sleep,
    load_checkpoint,
    save_checkpoint,
    append_jsonl,
    read_jsonl,
)

SONG_DETAIL_URL = "https://music.163.com/api/song/detail"
LYRIC_URL = "https://music.163.com/api/song/lyric"
ARTIST_SONGS_URL = "https://music.163.com/api/v1/artist/songs"

TIMESTAMP_RE = re.compile(r"\[\d{2}:\d{2}[.:]\d{2,3}\]")


def clean_lyric(raw_lyric):
    """去掉 LRC 时间轴标签，只保留歌词文本；过滤掉纯元信息行（作词/作曲等可保留，按需可再过滤）。"""
    if not raw_lyric:
        return ""
    lines = []
    for line in raw_lyric.splitlines():
        text = TIMESTAMP_RE.sub("", line).strip()
        if text:
            lines.append(text)
    return "\n".join(lines)


def fetch_more_song_ids(singer_id, limit=60):
    data = get_json(ARTIST_SONGS_URL, params={"id": singer_id, "order": "hot", "limit": limit, "offset": 0})
    if not data or "songs" not in data:
        return []
    return [s.get("id") for s in data["songs"] if s.get("id")]


def fetch_song_details(song_ids):
    """批量获取歌曲详情，一次最多传约 50 个 id，网易接口需要 ids=[1,2,3] 这种字符串格式。"""
    if not song_ids:
        return []
    ids_param = "[" + ",".join(str(i) for i in song_ids) + "]"
    data = get_json(SONG_DETAIL_URL, params={"ids": ids_param})
    if not data or "songs" not in data:
        return []
    return data["songs"]


def fetch_lyric(song_id):
    data = get_json(LYRIC_URL, params={"id": song_id, "lv": 1, "kv": 1, "tv": -1})
    if not data:
        return ""
    raw = (data.get("lrc") or {}).get("lyric", "")
    return clean_lyric(raw)


def chunked(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def main(per_singer, total_target):
    singers = read_jsonl("singers.jsonl")
    if not singers:
        print("请先运行 crawl_singers.py 生成 data/singers.jsonl")
        return

    ckpt = load_checkpoint()
    done_song_ids = set(ckpt.get("song_ids_done", []))
    existing = {r["song_id"] for r in read_jsonl("songs.jsonl")}
    done_song_ids |= existing

    total_saved = len(done_song_ids)

    for singer in singers:
        if total_saved >= total_target:
            break
        sid = singer["singer_id"]
        sname = singer["name"]

        candidate_ids = list(singer.get("hot_song_ids", []))
        if len(candidate_ids) < per_singer:
            candidate_ids += fetch_more_song_ids(sid, limit=per_singer + 10)
            polite_sleep()
        # 去重，且跳过已经爬过的
        candidate_ids = [i for i in dict.fromkeys(candidate_ids) if i not in done_song_ids]
        candidate_ids = candidate_ids[:per_singer]

        if not candidate_ids:
            print(f"[警告] 歌手《{sname}》没有可用歌曲 id，跳过（该歌手将不满足“至少一首歌”的要求，建议人工检查）")
            continue

        saved_for_this_singer = 0
        for batch in chunked(candidate_ids, 20):
            details = fetch_song_details(batch)
            polite_sleep()
            for song in details:
                song_id = song.get("id")
                if not song_id or song_id in done_song_ids:
                    continue
                lyric = fetch_lyric(song_id)
                polite_sleep(0.6, 1.3)
                if not lyric:
                    continue  # 要求 2000 首歌曲都要有歌词，没有歌词的直接跳过
                album = song.get("album", {})
                img_raw = album.get("picUrl", "")
                local_img = download_image(img_raw, f"song_{song_id}.jpg")
                record = {
                    "song_id": song_id,
                    "name": song.get("name", ""),
                    "singer_id": sid,
                    "singer_name": sname,
                    "lyric": lyric,
                    "img_url_raw": img_raw,
                    "local_image": local_img,
                    "source_url": f"https://music.163.com/#/song?id={song_id}",
                }
                append_jsonl("songs.jsonl", record)
                done_song_ids.add(song_id)
                saved_for_this_singer += 1
                total_saved += 1
                ckpt["song_ids_done"] = list(done_song_ids)
                save_checkpoint(ckpt)
                if total_saved % 20 == 0:
                    print(f"[进度] 已爬取歌曲 {total_saved} / {total_target}")
                if total_saved >= total_target:
                    break
            if total_saved >= total_target:
                break
        print(f"[歌手完成] 《{sname}》 贡献 {saved_for_this_singer} 首歌曲，累计 {total_saved}")

    print(f"歌曲爬取结束，共获得 {total_saved} 首歌曲，数据在 crawler/data/songs.jsonl")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-singer", type=int, default=25, help="每个歌手最多爬取的歌曲数")
    parser.add_argument("--total", type=int, default=2100, help="歌曲总数目标（比2000多留余量）")
    args = parser.parse_args()
    main(args.per_singer, args.total)
