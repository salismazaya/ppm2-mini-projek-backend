from rest_framework import serializers
from core.models import User, Comment, Like, Thread


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
        fields = ('id', 'username', 'first_name', 'last_name')


class UserEditSerializer(serializers.Serializer):
    # class Meta:
    #     model = User
    #     fields = ('id', 'username', 'first_name', 'last_name')
    id = serializers.IntegerField(read_only = True)
    username = serializers.CharField(required = False)
    first_name = serializers.CharField(required = False)
    last_name = serializers.CharField(required = False)



class CommentMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('id', 'user', 'text')

    user = UserSerializer(read_only = True)



class LikeSerializer(serializers.Serializer):
    thread = serializers.IntegerField()


class ThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Thread
        fields = ('id', 'owner', 'text', 'comments', 'likes_count', 'comments_count', 'liked')
        read_only_fields = ('comments', 'likes_count', 'comments_count')
    
    likes_count = serializers.IntegerField(read_only = True)
    comments_count = serializers.IntegerField(read_only = True)
    comments = serializers.ListSerializer(child = CommentMinimalSerializer(), read_only = True)
    owner = UserSerializer(read_only = True)
    liked = serializers.BooleanField(read_only = True)

    def create(self, validated_data):
        validated_data['owner'] = self.context.get('request').user
        return super().create(validated_data)

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('id', 'user', 'thread', 'text')

    user = UserSerializer(read_only = True)
    thread = serializers.IntegerField()
        