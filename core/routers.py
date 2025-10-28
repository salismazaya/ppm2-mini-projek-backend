from rest_framework import routers
from core.viewsets import CommentViewSet, ThreadViewSet, LikeViewSet

router = routers.DefaultRouter()
router.register(r'comments', CommentViewSet, basename = 'comment')
router.register(r'threads', ThreadViewSet)
router.register(r'likes', LikeViewSet, basename = 'likes')

