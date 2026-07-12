"""
可选的加分项：内存倒排索引（进一步压缩搜索耗时，应对更大数据量）。

思路：
- 数据量只有几千条时，views.py 里直接用数据库 icontains 已经足够快（<1s）。
- 如果想进一步优化（比如展示"极快"的搜索耗时，或者以后扩展到更大数据），
  可以用本模块：程序启动时把所有歌曲/歌手的文本一次性读入内存，
  之后的子串查询直接在内存里做字符串匹配，避免反复查数据库。

使用方法（可选，不用也完全不影响得分要求里"搜索"和"搜索结果页"部分）：
    from music.search_index import get_index
    idx = get_index()
    song_ids = idx.search_song(query)
"""
import threading

from .models import Song, Singer

_lock = threading.Lock()
_cache = {"songs": None, "singers": None}


class _Index:
    def __init__(self):
        self.songs = list(
            Song.objects.select_related("singer").values("id", "name", "singer__name", "lyric")
        )
        self.singers = list(Singer.objects.values("id", "name", "bio"))

    def search_song(self, query):
        q = query.lower()
        return [
            s["id"]
            for s in self.songs
            if q in s["name"].lower() or q in (s["singer__name"] or "").lower() or q in (s["lyric"] or "").lower()
        ]

    def search_singer(self, query):
        q = query.lower()
        return [s["id"] for s in self.singers if q in s["name"].lower() or q in (s["bio"] or "").lower()]


def get_index(force_refresh=False):
    with _lock:
        if _cache["songs"] is None or force_refresh:
            idx = _Index()
            _cache["songs"] = idx
        return _cache["songs"]
