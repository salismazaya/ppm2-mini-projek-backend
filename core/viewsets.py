from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from core.models import Comment, Thread, Like, User
from rest_framework.authtoken.models import Token
from core.serializers import CommentSerializer, ThreadSerializer, LikeSerializer, LoginSerializer, RegisterSerializer
from django.db.models import Count, Q, ExpressionWrapper, BooleanField
from rest_framework.response import Response
from django.http import HttpRequest

class CommentViewSet(viewsets.ViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def create(self, request: HttpRequest):
        cleaned_data = self.serializer_class(data = request.data)
        if not cleaned_data.is_valid():
            return Response(data = cleaned_data.errors, status = 400)

        comment = self.queryset.model.objects.create(
            user = request.user,
            text = cleaned_data['text'].value
        )

        thread_id = cleaned_data['thread'].value
        thread = Thread.objects.get(pk = thread_id)
        thread.comments.add(comment)

        return Response(data = cleaned_data.data)
    
    def destroy(self, request: HttpRequest, pk = None):
        user = request.user
        comment = Comment.objects.filter(pk = pk).first()
        thread = Thread.objects.filter(comments__user__in = [user.pk]).first()

        if comment is None or thread is None:
            return Response(status = 404, data = {'detail': 'Komentar tidak ditemukan'})

        can_destroyed = comment.user.pk == user.pk or \
                        thread.owner.pk == user.pk
        
        if not can_destroyed:
            return Response(status = 403, data = {'detail': 'Tidak bisa menghapus komentar ini'})
        
        # thread.comments
        comment.delete()
        return Response(status = 204, data = {})


class LikeViewSet(viewsets.ViewSet):
    serializer_class = LikeSerializer

    def create(self, request):
        cleaned_data = self.serializer_class(data = request.data)
        if not cleaned_data.is_valid():
            return Response(data = cleaned_data.errors, status = 400)
 
        thread_id = cleaned_data['thread'].value
        thread = Thread.objects.filter(pk = thread_id).first()

        if thread.likes.filter(user__pk = request.user.pk).exists():
            return Response(data = {'detail': 'Sudah di-like'}, status = 403)

        like = Like.objects.create(user = request.user)
        thread.likes.add(like)

        return Response(data = cleaned_data.data)

    def destroy(self, request, pk = None):
        # Like.objects.filter(pk = pk).delete()
        Thread.objects.get(pk = pk).likes.filter(user__pk = request.user.pk).delete()
        return Response(status = 204)


class ThreadViewSet(viewsets.ModelViewSet):
    queryset = Thread.objects.annotate(
        likes_count = Count('likes'),
        comments_count = Count('comments'),
    ).all()
    serializer_class = ThreadSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset.annotate(
            liked = ExpressionWrapper(
                Count('likes', filter = Q(likes__user__in = [user.pk])),
                output_field = BooleanField()
            )
        )
        return queryset
    
class LoginViewSet(APIView):
    permission_classes = [~permissions.IsAuthenticated]

    def post(self, request):
        serializer = LoginSerializer(data = request.data)
        
        if not serializer.is_valid():
            return Response(data = serializer.errors, status = 400)
        
        username = serializer['username'].value
        password = serializer['password'].value

        user = User.objects.filter(username = username).first()
        if user is None:
            return Response(data = {"detail": "Wrong username/password"}, status = 401)

        if not user.check_password(password):
            return Response(data = {"detail": "Wrong username/password"}, status = 401)

        Token.objects.filter(user__pk = user.pk).delete()
        token = Token.objects.create(user = user)
        return Response({'token': token.key})


class RegisterViewset(APIView):
    permission_classes = [~permissions.IsAuthenticated]

    def post(self, request):
        serializer = RegisterSerializer(data = request.data)

        if not serializer.is_valid():
            return Response(data = serializer.errors, status = 400)
        
        username = serializer['username'].value
        password = serializer['password'].value
        name = serializer['name'].value

        is_username_exists = User.objects.filter(username = username).exists()
        if is_username_exists:
            return Response(data = {'detail': 'Username sudah dipakai'}, status = 400)
        
        first_name, last_name = name.split(" ", 1)
        new_user = User(
            first_name = first_name,
            last_name = last_name,
            username = username
        )
        new_user.set_password(password)
        new_user.save()

        return Response(status = 201, data = {})

        
