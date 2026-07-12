# -*- coding: utf-8 -*-
"""
爬虫公共工具模块
- 随机 User-Agent
- 带重试的请求封装
- 断点续爬（把已经爬到的 id 记录在本地文件里）
"""
import json
import os
import random
import time

import requests

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

BASE_HEADERS = {
    "Referer": "https://music.163.com/",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Cookie": "appver=8.9.70;",  # 部分接口需要一个非空的 appver cookie 才会返回完整数据
}

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
IMG_DIR = os.path.join(DATA_DIR, "images")
CHECKPOINT_FILE = os.path.join(DATA_DIR, "checkpoint.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)


def random_headers():
    h = dict(BASE_HEADERS)
    h["User-Agent"] = random.choice(USER_AGENTS)
    return h


def polite_sleep(a=1.0, b=2.2):
    """两次请求之间的随机间隔，避免过于频繁地访问目标站点。"""
    time.sleep(random.uniform(a, b))


def get_json(url, params=None, max_retry=3, timeout=10):
    """带重试的 GET 请求，返回解析后的 JSON（失败返回 None）。"""
    for attempt in range(1, max_retry + 1):
        try:
            resp = requests.get(url, params=params, headers=random_headers(), timeout=timeout)
            resp.encoding = "utf-8"
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"[警告] 状态码 {resp.status_code}，第 {attempt} 次重试: {url}")
        except Exception as e:
            print(f"[警告] 请求异常 {e}，第 {attempt} 次重试: {url}")
        polite_sleep(1.5, 3.0)
    print(f"[错误] 多次重试仍失败，跳过: {url} params={params}")
    return None


def download_image(url, save_name):
    """下载图片到本地 data/images 目录，返回相对路径；失败返回空字符串。"""
    if not url:
        return ""
    path = os.path.join(IMG_DIR, save_name)
    if os.path.exists(path):
        return f"images/{save_name}"
    try:
        resp = requests.get(url, headers=random_headers(), timeout=10)
        if resp.status_code == 200:
            with open(path, "wb") as f:
                f.write(resp.content)
            return f"images/{save_name}"
    except Exception as e:
        print(f"[警告] 图片下载失败 {url}: {e}")
    return ""


def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"singer_ids_done": [], "song_ids_done": []}


def save_checkpoint(ckpt):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(ckpt, f, ensure_ascii=False, indent=2)


def append_jsonl(filename, record):
    """以追加方式写入一条 JSON 记录（每行一条），程序中断也不会丢失已爬数据。"""
    path = os.path.join(DATA_DIR, filename)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
