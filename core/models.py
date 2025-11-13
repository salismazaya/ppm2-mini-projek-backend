from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    profile_picture = models.FileField(null = True, blank = True, upload_to = "uploads")


class Thread(models.Model):
    owner = models.ForeignKey(User, on_delete = models.CASCADE)
    text = models.TextField()
    tags = models.CharField(null = True, blank = True, max_length = 255)
    title = models.CharField(max_length = 255, null = True, blank = True)
    file = models.FileField(null = True, blank = True, upload_to = "uploads")
    created_at = models.DateTimeField(default = timezone.now)

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
    created_at = models.DateTimeField(default = timezone.now)


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    text = models.TextField()
    thread = models.ForeignKey(Thread, on_delete = models.CASCADE)
    file = models.FileField(null = True, blank = True, upload_to = "uploads")
    created_at = models.DateTimeField(default = timezone.now)
