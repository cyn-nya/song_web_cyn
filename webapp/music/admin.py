from django.contrib import admin
from .models import Singer, Song, Comment

admin.site.register(Singer)
admin.site.register(Song)
admin.site.register(Comment)
