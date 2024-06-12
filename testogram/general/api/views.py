from rest_framework.viewsets import GenericViewSet, ModelViewSet
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response


from general.models import User, Post, Comment, Chat, Message
from general.api.serializers import ( UserRegistrationSerializer, UserListSerializer, UserRetrieveSerializer,
                                     PostCreateUpdateSerializer, PostListSerializer, PostRetrieveSerializer,
                                     CommentSerializer, ReactionSerializer, ChatSerializer, MessageListSerializer,
                                     ChatListSerializer, MessageSerializer

                                      )


from rest_framework.mixins import ( CreateModelMixin, ListModelMixin, RetrieveModelMixin, UpdateModelMixin,
                                   DestroyModelMixin
                                    )

from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import F, Case, When, CharField, Value, Q, OuterRef, Subquery


# На уровне View определяется логика обработки HTTP запросов и возвращения ответов.
# Также определяется, для каких запросов какие сериализаторы используются и многое другое.


# Получение списка объектов реализовано в ListModelMixin
class UserViewSet(
    CreateModelMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    В классах viewset есть два определения сериализатора:
    1) в виде поля serializer_class.
    2) в виде метода get_serializer_class.
    """

    queryset = User.objects.all().order_by('-id')

    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [AllowAny] # дает доступ к эндпоинту без аутентификации
        else: # В остальных случаях будет доступ только для аутентифицированных пользователей.
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    example = """permission_classes = [IsAuthenticated] # Второй вариант использования permissions
                def get_permissions(self):
                    if self.action == "create":
                        self.permission_classes = [AllowAny]
                    return super().get_permissions() """
    
    def get_queryset(self):
        queryset = User.objects.all().prefetch_related(
            "friends", ).order_by("-id")
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        if self.action in ["retrieve", "me"]:
            return UserRetrieveSerializer
        return UserListSerializer
    
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        instance = self.request.user 
        # мы берем пользователя из запроса. А он там есть, потому что для выполнения этого запроса пользователь положит в хедер свой токен.
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=["get"])
    def friends(self, request, pk=None):
        user = self.get_object()
        queryset = self.filter_queryset(
            self.get_queryset().filter(friends=user)
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"])
    def add_friend(self, request, pk=None):
        user = self.get_object()
        request.user.friends.add(user)
        return Response('Friend added')

    @action(detail=True, methods=["post"])
    def remove_friend(self, request, pk=None):
        """
        Пользователь, которого добавляем в друзья или удаляем из друзей, будет определяться при помощи lookup, поэтому detail=True.
        Будут выполняться запросы POST "api/users/<user_id>/add_friend/" и POST "api/users/<user_id>/remove_friend".
        """
        user = self.get_object()
        request.user.friends.remove(user)
        return Response("Friend removed")
    

class PostViewSet(ModelViewSet):
    queryset = Post.objects.all().order_by("-id")
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer
        elif self.action == "retrieve":
            return PostRetrieveSerializer
        return PostCreateUpdateSerializer
    
    def perform_update(self, serializer):
        instance = self.get_object()

        if instance.author != self.request.user:
            raise PermissionDenied("Вы не являетесь автором этого поста.")
        serializer.save()
    
    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("Вы не являетесь автором этого поста.")
        instance.delete()

class CommentsViewSet(
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    GenericViewSet,
):
    """
    Если нам нужно получить все комментарии, то можем выполнить запрос GET /api/comments/.
    Если же у нас есть ID поста (допустим id=100), то мы можем выполнить запрос GET /api/comments/?post__id=100 и получить все комментарии к этому посту.
    """
    queryset = Comment.objects.all().order_by("-id")
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer
    filter_backends = [DjangoFilterBackend] #стандартный бэкенд для фильтров. Он нужен для того, чтобы в эндпоинт включить стандартную фильтрацию
    filterset_fields = ["post__id"] # в поле filterset_fields мы можем указать, по какому параметру мы можем фильтровать список комментариев

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("Вы не являетесь автором этого комментария.")
        instance.delete()


class ReactionViewSet(
    CreateModelMixin, GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    serializer_class = ReactionSerializer


class ChatViewSet(
    CreateModelMixin,
    GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatSerializer




class ChatViewSet(
    CreateModelMixin,
    ListModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return ChatListSerializer
        if self.action == "messages":
            return MessageListSerializer
        return ChatSerializer
    
    def get_queryset(self):
        user = self.request.user

        last_message_subquery = Message.objects.filter(
            chat=OuterRef('pk')
        ).order_by('-created_at').values('created_at')[:1]
        last_message_content_subquery = Message.objects.filter(
            chat=OuterRef('pk')
        ).order_by('-created_at').values('content')[:1]

        qs = Chat.objects.filter(
            Q(user_1=user) | Q(user_2=user),
            messages__isnull=False,
        ).annotate(
            last_message_datetime=Subquery(last_message_subquery),
            last_message_content=Subquery(last_message_content_subquery),
        ).select_related(
            "user_1",
            "user_2",
        ).order_by("-last_message_datetime").distinct()
        return qs
    
    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        messages = self.get_object().messages.filter(chat__id=pk).annotate(
            message_author=Case(
                When(author=self.request.user, then=Value("Вы")),
                default=F("author__first_name"),
                output_field=CharField(),
            )
        ).order_by("-created_at")
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

class MessageViewSet(
    CreateModelMixin,
    DestroyModelMixin,
    GenericViewSet,
):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    queryset = Message.objects.all().order_by("-id")

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("Вы не являетесь автором этого сообщения.")
        instance.delete()