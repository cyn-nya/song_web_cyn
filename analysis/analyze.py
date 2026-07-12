# -*- coding: utf-8 -*-
"""
数据分析脚本：从爬虫数据（crawler/data/songs.jsonl, singers.jsonl）出发，
产出 3 个可视化结论，图表保存到 analysis/output/ 目录。

运行前需要：
    pip install jieba matplotlib numpy wordcloud   (wordcloud 可选)

用法：
    cd analysis
    python analyze.py
"""
import json
import os
from collections import Counter

import matplotlib.pyplot as plt
import numpy as np

# 让中文正常显示（Windows 上一般自带微软雅黑）
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "crawler", "data")
OUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUT_DIR, exist_ok=True)


def load_jsonl(name):
    path = os.path.join(DATA_DIR, name)
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def conclusion_1_songs_per_singer(songs):
    """结论一：不同歌手的歌曲数量分布 —— 观察平台上"腰部/头部"歌手的分布是否符合长尾规律。"""
    counter = Counter(s["singer_name"] for s in songs)
    counts = sorted(counter.values(), reverse=True)

    plt.figure(figsize=(8, 5))
    plt.plot(range(1, len(counts) + 1), counts, marker="o", markersize=3)
    plt.xlabel("歌手排名（按收录歌曲数从多到少）")
    plt.ylabel("收录歌曲数量")
    plt.title("歌手收录歌曲数量的长尾分布")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "conclusion1_long_tail.png"), dpi=150)
    plt.close()

    top5 = counter.most_common(5)
    total = sum(counter.values())
    top5_ratio = sum(c for _, c in top5) / total * 100
    print(f"[结论一] 收录歌曲最多的前 5 位歌手: {top5}")
    print(f"[结论一] 前5位歌手贡献了全部歌曲的 {top5_ratio:.1f}%")


def conclusion_2_lyric_length_distribution(songs):
    """结论二：歌词长度（字数）的分布情况，并按歌手分组比较均值，观察是否存在明显差异。"""
    lengths = [len(s["lyric"].replace("\n", "")) for s in songs if s.get("lyric")]

    plt.figure(figsize=(8, 5))
    plt.hist(lengths, bins=30, color="#e0234e", edgecolor="white")
    plt.xlabel("歌词字数")
    plt.ylabel("歌曲数量")
    plt.title("歌曲歌词长度分布直方图")
    plt.axvline(float(np.mean(lengths)), color="black", linestyle="--", label=f"均值={np.mean(lengths):.0f}字")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "conclusion2_lyric_length.png"), dpi=150)
    plt.close()

    print(f"[结论二] 歌词长度均值 {np.mean(lengths):.1f} 字，中位数 {np.median(lengths):.1f} 字，"
          f"标准差 {np.std(lengths):.1f}")


def conclusion_3_hot_words(songs):
    """结论三：对所有歌词分词后统计高频词（词云/柱状图），观察全体歌词的主题倾向。
    需要 jieba；若未安装则退化为按字符统计（仅供参照）。
    """
    all_lyrics = "\n".join(s.get("lyric", "") for s in songs)
    try:
        import jieba
        words = [w for w in jieba.cut(all_lyrics) if len(w.strip()) > 1]
    except ImportError:
        print("[提示] 未安装 jieba，使用简单的双字符切分作为替代（建议 pip install jieba 获得更准确结果）")
        cleaned = "".join(ch for ch in all_lyrics if ch.strip())
        words = [cleaned[i : i + 2] for i in range(0, len(cleaned) - 1, 2)]

    # 一个很小的停用词表，可以自行扩充
    stopwords = {"我们", "你们", "他们", "一个", "没有", "什么", "这个", "那个", "自己", "就是", "还是"}
    words = [w for w in words if w not in stopwords]

    counter = Counter(words)
    top20 = counter.most_common(20)

    labels = [w for w, _ in top20]
    values = [c for _, c in top20]

    plt.figure(figsize=(10, 6))
    plt.barh(labels[::-1], values[::-1], color="#2d2d44")
    plt.xlabel("出现次数")
    plt.title("歌词高频词 Top 20")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "conclusion3_hot_words.png"), dpi=150)
    plt.close()

    print(f"[结论三] 歌词高频词 Top 10: {top20[:10]}")

    # 可选：生成词云（需要 pip install wordcloud，且需要一个中文字体文件）
    try:
        from wordcloud import WordCloud

        wc = WordCloud(
            width=900,
            height=600,
            background_color="white",
            font_path="C:/Windows/Fonts/msyh.ttc",  # Windows 微软雅黑；若在其他系统上运行请改成对应字体路径
        ).generate_from_frequencies(dict(counter.most_common(200)))
        wc.to_file(os.path.join(OUT_DIR, "conclusion3_wordcloud.png"))
        print("[提示] 词云已生成: conclusion3_wordcloud.png")
    except Exception as e:
        print(f"[提示] 跳过词云生成（可选项）: {e}")


def main():
    songs = load_jsonl("songs.jsonl")
    if not songs:
        print("没有找到 crawler/data/songs.jsonl，请先运行爬虫。")
        return
    print(f"共加载 {len(songs)} 首歌曲用于分析\n")

    conclusion_1_songs_per_singer(songs)
    conclusion_2_lyric_length_distribution(songs)
    conclusion_3_hot_words(songs)

    print(f"\n所有图表已保存到: {OUT_DIR}")


if __name__ == "__main__":
    main()
