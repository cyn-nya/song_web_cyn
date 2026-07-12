from django.db import models


class Singer(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    image = models.CharField(max_length=500, blank=True)  # 存相对/绝对图片路径或URL
    bio = models.TextField(blank=True)
    source_url = models.URLField(max_length=500, blank=True)

    def __str__(self):
        return self.name


class Song(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    singer = models.ForeignKey(Singer, on_delete=models.CASCADE, related_name="songs")
    lyric = models.TextField(blank=True)
    image = models.CharField(max_length=500, blank=True)
    source_url = models.URLField(max_length=500, blank=True)

    def __str__(self):
        return f"{self.name} - {self.singer.name}"


class Comment(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name="comments")
    content = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]  # 最新评论在前

    def __str__(self):
        return f"Comment on {self.song.name}: {self.content[:20]}"
