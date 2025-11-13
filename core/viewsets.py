from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from core.models import Comment, Thread, Like, User, PhotoProfile
from rest_framework.authtoken.models import Token
from core.serializers import CommentSerializer, ThreadSerializer, \
    LikeSerializer, LoginSerializer, RegisterSerializer, UserEditSerializer, UserSerializer
from django.db.models import Count, Subquery, OuterRef, Exists, IntegerField, F
from django.db.models.functions import Coalesce
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from django.http import HttpRequest, HttpResponse
from core.helpers import appscript_storage
from django.forms import model_to_dict
from core.helpers import appscript_storage
from django.conf import settings
import base64


class UserViewSet(APIView):
    authentication_classes = [TokenAuthentication]

    class UserProfiledProxy:
        def __init__(self, user):
            self.__user = user

        def __getattr__(self, key):
            return getattr(self.__user, key)
        
        @property
        def photo(self):
            pp = PhotoProfile.objects.filter(user__pk = self.__user.pk).first()
            if pp is None:
                return
            
            return pp.media_id
        
        def update_photo(self, file_id: str):
            # print(self.__user)
            PhotoProfile.objects.update_or_create(user__pk = self.__user.pk, defaults = {
                'user_id': self.__user.pk,
                'media_id': file_id
            })

    def get(self, request: HttpRequest, format = None):
        user = UserViewSet.UserProfiledProxy(request.user)

        serializer = UserSerializer(data = model_to_dict(user))
        serializer.is_valid() # always valid

        result = {
            'photo': user.photo,
            'id': user.pk,
            **serializer.data
        }

        return Response(data = result)
    
    def put(self, request: HttpRequest):
        user = UserViewSet.UserProfiledProxy(request.user)
        serializer = UserEditSerializer(data = request.data)
        
        if not serializer.is_valid():
            return Response(data = serializer.errors, status = 400)
        
        photo = serializer.data.get('photo')
        data = {**serializer.data}

        username = data.get('username')
        if user.username != username and username:
            is_username_exists = User.objects.filter(username = username).exists()
            if is_username_exists:
                return Response(data = {'detail': 'Username sudah digunakan'}, status = 403)

        if photo:
            photo_bytes = base64.b64decode(photo)
            file = appscript_storage.upload_file(photo_bytes, serializer.data.get('photo_extension'))

            user.update_photo(file.file_id)

            del data['photo']
            del data['photo_extension']

        User.objects.filter(pk = user.pk).update(**data)
        return Response(status = 200, data = {'status': 'OK'})


class CommentViewSet(viewsets.ViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    authentication_classes = [TokenAuthentication]

    def create(self, request: HttpRequest):
        cleaned_data = self.serializer_class(data = request.data)
        if not cleaned_data.is_valid():
            return Response(data = cleaned_data.errors, status = 400)
        
        thread_id = cleaned_data['thread'].value

        self.queryset.model.objects.create(
            user = request.user,
            text = cleaned_data['text'].value,
            thread_id = thread_id
        )

        return Response(data = cleaned_data.data)
    
    def destroy(self, request: HttpRequest, pk = None):
        user = request.user
        comment = Comment.objects.filter(pk = pk).first()
        thread = comment.thread

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
    authentication_classes = [TokenAuthentication]

    def create(self, request: HttpRequest):
        cleaned_data = self.serializer_class(data = request.data)
        if not cleaned_data.is_valid():
            return Response(data = cleaned_data.errors, status = 400)
 
        thread_id = cleaned_data['thread'].value
        # thread = Thread.objects.filter(pk = thread_id).first()

        if Like.objects.filter(
            user__pk = request.user.pk,
            thread__pk = thread_id,
        ).exists():
            return Response(data = {'detail': 'Sudah di-like'}, status = 403)

        Like.objects.create(user = request.user, thread_id = thread_id)
        # thread.likes.add(like)

        return Response(data = cleaned_data.data)

    def destroy(self, request, pk = None):
        Like.objects.filter(user__pk = request.user.pk, thread__pk = pk).delete()
        # Thread.objects.get(pk = pk).likes.filter(user__pk = request.user.pk).delete()
        return Response(status = 204, data = {})


likes_subquery = (
    Like.objects
        .filter(thread__pk = OuterRef('pk'))
        .values('thread')
        .annotate(count = Count('pk'))
        .values('count')
)

comments_subquery = (
    Comment.objects
        .filter(thread__pk = OuterRef('pk'))
        .values('thread')
        .annotate(count = Count('pk'))
        .values('count')
)


class ThreadViewSet(viewsets.ModelViewSet):
    queryset = Thread.objects.annotate(
        likes_count = Coalesce(Subquery(likes_subquery, output_field = IntegerField()), 0),
        comments_count = Coalesce(Subquery(comments_subquery, output_field = IntegerField()), 0),
    ).all()
    serializer_class = ThreadSerializer
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        order_by = self.request.GET.get('order', 'recent')
        user = self.request.user

        queryset = self.queryset.annotate(
            liked = Exists(
                Like.objects.filter(user__pk = user.pk).filter(thread__pk = OuterRef('pk'))[:1]
            )
        )

        if order_by == "trending":
            queryset = queryset.annotate(
                score = F('comments_count') + F('likes_count')
            ).order_by('-score')
        else:
            queryset = queryset.order_by('-id')

        return queryset
    
    def create(self, request: HttpRequest, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    
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

        
class FileViewset(APIView):
    def get(self, request: HttpRequest):
        file_id = request.GET['id']
        download = appscript_storage.download_file(file_id)
        
        response = HttpResponse(content = download.data, content_type = download.mimetype)

        if not download.mimetype.startswith('image/'):
            response.headers['Content-Dispotion'] = 'attachment; filename="%s"' % download.filename

        return response