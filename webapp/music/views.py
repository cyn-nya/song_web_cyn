import time

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404

from .models import Singer, Song, Comment

PAGE_SIZE = 20


def _paginate(request, queryset, page_size=PAGE_SIZE):
    paginator = Paginator(queryset, page_size)
    page_number = request.GET.get("page", 1)
    try:
        page_number = int(page_number)
    except (TypeError, ValueError):
        page_number = 1
    page_number = max(1, min(page_number, paginator.num_pages or 1))
    return paginator.get_page(page_number)


def song_list(request):
    songs = Song.objects.select_related("singer").order_by("id")
    page_obj = _paginate(request, songs)
    return render(request, "music/song_list.html", {"page_obj": page_obj})


def song_detail(request, song_id):
    song = get_object_or_404(Song.objects.select_related("singer"), id=song_id)
    comments = song.comments.all()
    return render(request, "music/song_detail.html", {"song": song, "comments": comments})


def add_comment(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    if request.method == "POST":
        content = (request.POST.get("content") or "").strip()
        if content:
            Comment.objects.create(song=song, content=content[:1000])
    return redirect("song_detail", song_id=song.id)


def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    song_id = comment.song_id
    if request.method == "POST":
        comment.delete()
    return redirect("song_detail", song_id=song_id)


def singer_list(request):
    singers = Singer.objects.order_by("id")
    page_obj = _paginate(request, singers)
    return render(request, "music/singer_list.html", {"page_obj": page_obj})


def singer_detail(request, singer_id):
    singer = get_object_or_404(Singer, id=singer_id)
    songs = singer.songs.all().order_by("id")
    return render(request, "music/singer_detail.html", {"singer": singer, "songs": songs})


def search(request):
    """
    简单精确子串搜索：
    - type=song: 在歌曲名/歌手名/歌词中查找子串
    - type=singer: 在歌手名/简介中查找子串
    数据规模在数千条时，直接用数据库 icontains 子串查询即可在 1 秒内返回，
    不需要额外建索引；如果以后数据量变大，可以把这里换成 search/search_index.py
    里的倒排索引实现（已经写好，import build_index / search_index 即可切换）。
    """
    query = (request.GET.get("q") or "").strip()[:20]
    search_type = request.GET.get("type", "song")
    if search_type not in ("song", "singer"):
        search_type = "song"

    results = []
    elapsed_ms = 0
    if query:
        start = time.perf_counter()
        if search_type == "song":
            qs = Song.objects.select_related("singer").filter(
                Q(name__icontains=query) | Q(singer__name__icontains=query) | Q(lyric__icontains=query)
            ).order_by("id")
        else:
            qs = Singer.objects.filter(
                Q(name__icontains=query) | Q(bio__icontains=query)
            ).order_by("id")
        results = list(qs)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

    page_obj = _paginate(request, results)
    return render(
        request,
        "music/search_results.html",
        {
            "query": query,
            "search_type": search_type,
            "page_obj": page_obj,
            "result_count": len(results),
            "elapsed_ms": elapsed_ms,
        },
    )
