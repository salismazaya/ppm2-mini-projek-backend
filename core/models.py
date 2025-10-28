from django.db import models
from django.contrib.auth.models import User


class Like(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    text = models.TextField()


class Thread(models.Model):
    owner = models.ForeignKey(User, on_delete = models.CASCADE)
    text = models.TextField()
    likes = models.ManyToManyField(Like, blank = True)
    comments = models.ManyToManyField(Comment, blank = True)
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



