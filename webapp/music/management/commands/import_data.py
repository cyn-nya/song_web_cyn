"""
把 crawler/data/singers.jsonl 和 crawler/data/songs.jsonl 导入 Django 数据库，
并把 crawler/data/images 里的图片复制到 Django 的 media 目录。

用法（在 webapp_src 目录下）：
    python manage.py import_data --crawler-dir ../crawler/data
"""
import json
import os
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand

from music.models import Singer, Song


class Command(BaseCommand):
    help = "导入爬虫产出的 jsonl 数据到数据库"

    def add_arguments(self, parser):
        parser.add_argument(
            "--crawler-dir",
            default=os.path.join(settings.BASE_DIR, "..", "crawler", "data"),
            help="crawler/data 目录路径（里面应有 singers.jsonl / songs.jsonl / images/）",
        )

    def handle(self, *args, **options):
        crawler_dir = os.path.abspath(options["crawler_dir"])
        singers_path = os.path.join(crawler_dir, "singers.jsonl")
        songs_path = os.path.join(crawler_dir, "songs.jsonl")
        images_src_dir = os.path.join(crawler_dir, "images")
        images_dst_dir = os.path.join(settings.MEDIA_ROOT, "images")
        os.makedirs(images_dst_dir, exist_ok=True)

        if not os.path.exists(singers_path):
            self.stderr.write(f"找不到 {singers_path}，请先运行爬虫")
            return

        singer_id_map = {}  # 爬虫的 singer_id -> Django 数据库里的主键
        with open(singers_path, "r", encoding="utf-8") as f:
            count = 0
            for line in f:
                record = json.loads(line)
                local_image = record.get("local_image", "")
                if local_image:
                    src = os.path.join(crawler_dir, local_image)
                    if os.path.exists(src):
                        shutil.copy(src, os.path.join(images_dst_dir, os.path.basename(local_image)))
                        local_image = f"images/{os.path.basename(local_image)}"
                singer_obj, _ = Singer.objects.update_or_create(
                    name=record["name"],
                    defaults={
                        "image": local_image,
                        "bio": record.get("bio", ""),
                        "source_url": record.get("source_url", ""),
                    },
                )
                singer_id_map[record["singer_id"]] = singer_obj.id
                count += 1
        self.stdout.write(self.style.SUCCESS(f"导入歌手 {count} 位"))

        if not os.path.exists(songs_path):
            self.stderr.write(f"找不到 {songs_path}，请先运行爬虫")
            return

        with open(songs_path, "r", encoding="utf-8") as f:
            count = 0
            skipped = 0
            for line in f:
                record = json.loads(line)
                singer_pk = singer_id_map.get(record["singer_id"])
                if not singer_pk:
                    skipped += 1
                    continue
                local_image = record.get("local_image", "")
                if local_image:
                    src = os.path.join(crawler_dir, local_image)
                    if os.path.exists(src):
                        shutil.copy(src, os.path.join(images_dst_dir, os.path.basename(local_image)))
                        local_image = f"images/{os.path.basename(local_image)}"
                Song.objects.update_or_create(
                    name=record["name"],
                    singer_id=singer_pk,
                    defaults={
                        "lyric": record.get("lyric", ""),
                        "image": local_image,
                        "source_url": record.get("source_url", ""),
                    },
                )
                count += 1
        self.stdout.write(self.style.SUCCESS(f"导入歌曲 {count} 首（跳过 {skipped} 首找不到歌手的）"))
