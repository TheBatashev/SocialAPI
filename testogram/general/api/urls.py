from rest_framework.routers import SimpleRouter

from general.api.views import ( UserViewSet, PostViewSet, CommentsViewSet, ReactionViewSet, ChatViewSet,
                               MessageViewSet
                               
                               )


router = SimpleRouter() 
#Класс SimpleRouter определяет роуты для viewset классов. Он автоматически сопоставляет url-адреса с логикой в viewset классе



router.register(r'posts', PostViewSet, basename="posts")
router.register(r'comments', CommentsViewSet, basename="comments")
router.register(r'reaction', ReactionViewSet, basename="reaction")
router.register(r'users', UserViewSet, basename="users")
router.register(r'chats', ChatViewSet, basename="chats")
router.register(r'messages', MessageViewSet, basename="messages")


urlpatterns = router.urls