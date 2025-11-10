from django.db import models
from django.contrib.auth.models import User


class Thread(models.Model):
    owner = models.ForeignKey(User, on_delete = models.CASCADE)
    text = models.TextField()
    # likes = models.ManyToManyField(Like, blank = True)
    # comments = models.ManyToManyField(Comment, blank = True)
    # likes_count = models.GeneratedField(
    #     expression = models.Count('likes'),
    #     output_field = models.PositiveIntegerField(),
    #     db_persist = False
    # )
    # comments_count = models.GeneratedField(
    #     expression = models.Count('likes'),
    #     output_field = models.PositiveIntegerField(),
    #     db_persist = False
    # )

    def __str__(self):
        return f"<Thread {self.pk}: {self.text[:20]}>"

    @property
    def comments(self):
        return Comment.objects.filter(thread__pk = self.pk)


class Like(models.Model):
    class Meta:
        unique_together = ('user', 'thread')

    user = models.ForeignKey(User, on_delete = models.CASCADE)
    thread = models.ForeignKey(Thread, on_delete = models.CASCADE)


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    text = models.TextField()
    thread = models.ForeignKey(Thread, on_delete = models.CASCADE)