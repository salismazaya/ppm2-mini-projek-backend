from django.contrib import admin

from core.models import Comment, Thread, Like

admin.site.register(Comment)
admin.site.register(Thread)
admin.site.register(Like)
