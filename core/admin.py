from django.contrib import admin

from core.models import Comment, Thread, Like

class LikeInline(admin.StackedInline):
    model = Like
    extra = 0

class CommentInline(admin.StackedInline):
    model = Comment
    extra = 0


class ThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'text',)
    inlines = (LikeInline, CommentInline)
    search_fields = ('owner__username', 'owner__first_name', 'owner__last_name', 'text')


class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'text', 'thread')
    search_fields = ('text', 'thread__text', 'user__username', 'user__first_name', 'user__last_name')


class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'thread')
    search_fields = ('thread__text', 'user__username', 'user__first_name', 'user__last_name')


admin.site.register(Comment, CommentAdmin)
admin.site.register(Thread, ThreadAdmin)
admin.site.register(Like, LikeAdmin)
