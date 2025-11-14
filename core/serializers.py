from rest_framework import serializers
from core.models import User, Comment, Like, Thread
import mimetypes


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField()
    username = serializers.CharField()
    password = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'profile_picture', 'profile_picture_url')

    id = serializers.IntegerField(read_only = True)
    profile_picture = serializers.FileField(write_only = True, required = False)
    profile_picture_url = serializers.CharField(required = False)

    def validate_profile_picture(self, value):
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']

        # value adalah InMemoryUploadedFile atau TemporaryUploadedFile
        mime_type = mimetypes.guess_type(value.name)[0]

        if mime_type not in allowed_types:
            raise serializers.ValidationError(
                f"Invalid file type: {mime_type}. Allowed types: {', '.join(allowed_types)}"
            )

        # (opsional) batas ukuran file
        max_size = 2 * 1024 * 1024  # 2 MB
        if value.size > max_size:
            raise serializers.ValidationError("File too large. Max size is 2MB.")

        return value


class UserEditSerializer(UserSerializer):
    username = serializers.CharField(required = False)
    first_name = serializers.CharField(required = False)
    last_name = serializers.CharField(required = False)
    profile_picture_url = serializers.CharField(required = False, read_only = True)


class CommentMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('id', 'user', 'text', 'created_at', 'file')
        read_only_fields = ('id', 'created_at')

    user = UserSerializer(read_only = True)


class LikeSerializer(serializers.Serializer):
    thread = serializers.IntegerField()


class FileSerializer(serializers.Serializer):
    data = serializers.CharField()
    extension = serializers.CharField()


class ThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Thread
        fields = ('id', 'owner', 'title', 'text', 'comments', 'likes_count', 'comments_count', 'liked', 'created_at', 'file')
        read_only_fields = ('comments', 'likes_count', 'comments_count', 'liked', 'created_at', )
    
    likes_count = serializers.IntegerField(read_only = True)
    comments_count = serializers.IntegerField(read_only = True)
    comments = CommentMinimalSerializer(many = True, read_only = True)
    owner = UserSerializer(read_only = True)
    liked = serializers.BooleanField(read_only = True)


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('id', 'user', 'thread', 'text', 'created_at', 'file')
        read_only_fields = ('id', 'created_at',)

    user = UserSerializer(read_only = True)
    # thread = serializers.IntegerField()

        