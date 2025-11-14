from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from core.models import Comment, Thread, Like, User
from rest_framework.authtoken.models import Token
from core.serializers import CommentSerializer, ThreadSerializer, \
    LikeSerializer, LoginSerializer, RegisterSerializer, UserEditSerializer, UserSerializer
from django.db.models import Count, Subquery, OuterRef, Exists, IntegerField, F
from django.db.models.functions import Coalesce
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from django.http import HttpRequest, HttpResponse,  Http404
from rest_framework.parsers import MultiPartParser, FormParser
from core.helpers.upload import handle_uploaded_file, get_random_new_filename

from core.helpers import appscript_storage
from django.conf import settings
from django.forms import model_to_dict


class UserViewSet(APIView):
    authentication_classes = [TokenAuthentication]
    # parser_classes = [MultiPartParser, FormParser]

    def get(self, request: HttpRequest, format = None):
        user = request.user

        data = model_to_dict(user)
        
        if data.get('profile_picture'):
            data['profile_picture_url'] = data['profile_picture'].url
            del data['profile_picture']

        # print(data)
        if not data.get('profile_picture').name:
            del data['profile_picture'
                     ]
        serializer = UserSerializer(data = data)
        serializer.is_valid() # always valid

        # print(serializer.data['profile_picture'].url)
        result = {
            'id': user.pk,
            **serializer.data
        }

        return Response(data = result)
    
    def put(self, request: HttpRequest):
        user = request.user

        data = request.FILES
        data.update(request.data)

        serializer = UserEditSerializer(data = data)
        
        if not serializer.is_valid():
            return Response(data = serializer.errors, status = 400)

        serializer_data = serializer.data

        username = serializer_data.get('username')
        if user.username != username and username:
            is_username_exists = User.objects.filter(username = username).exists()
            if is_username_exists:
                return Response(data = {'detail': 'Username sudah digunakan'}, status = 403)

        profile_picture = data.get('profile_picture')

        if profile_picture:
            filename = get_random_new_filename(profile_picture.name)
            user.profile_picture.save(filename, profile_picture)
            del data['profile_picture']

        User.objects.filter(pk = user.pk).update(**data)
        return Response(status = 200, data = {'status': 'OK'})


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    authentication_classes = [TokenAuthentication]

    # def create(self, request: HttpRequest):
    #     cleaned_data = self.serializer_class(data = request.data)
    #     if not cleaned_data.is_valid():
    #         return Response(data = cleaned_data.errors, status = 400)
        
    #     thread_id = cleaned_data['thread'].value

    #     self.queryset.model.objects.create(
    #         user = request.user,
    #         text = cleaned_data['text'].value,
    #         thread_id = thread_id
    #     )

    #     return Response(data = cleaned_data.data)
    
    def perform_create(self, serializer):
        serializer.save(user_id = self.request.user.pk)

    def update(self, request: HttpRequest, *args, **kwargs):
        # return super().update(request, *args, **kwargs)
        raise NotImplementedError

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

    def destroy(self, request: HttpRequest, pk = None):
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
    ).select_related('owner')
    serializer_class = ThreadSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        return serializer.save(owner_id = self.request.user.pk)

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
    permission_classes = [permissions.AllowAny]

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

        return Response(status = 201, data = {'status': 'OK'})

import mimetypes
        

def media_files(request: HttpRequest, filename: str):
    filepath = settings.BASE_DIR / ("uploads/" + filename)

    try:
        with open(filepath, 'rb') as f:
            content = f.read()
            content_type, _ = mimetypes.guess_type(filepath)

            response = HttpResponse(content = content, content_type = content_type)

            if not content_type.startswith('image/'):
                response.headers['Content-Dispotion'] = 'attachment; filename="%s"' % filename

            return response
    except (FileNotFoundError, FileExistsError):
        raise Http404