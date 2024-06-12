from rest_framework.serializers import (Serializer, ModelSerializer, SerializerMethodField,
                                        CurrentUserDefault, HiddenField, CharField, DateTimeField
                                        )
from general.models import User, Post, Comment, Reaction, Chat, Message
from django.db.models import Q
from rest_framework.exceptions import ValidationError



class CommentSerializer(ModelSerializer):
    author = HiddenField(
        default=CurrentUserDefault(),
    )

    def get_fields(self):
        fields =  super().get_fields()
        if self.context["request"].method == "GET":
            fields['author'] = UserShortSerializer(read_only=True)
        return fields
    
    class Meta:
        model = Comment
        fields = (
            "id", "author", "post", "body", "created_at",
        )





class UserShortSerializer(ModelSerializer):
    # сериализатор для автора
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name",
        )

class PostListSerializer(ModelSerializer):
    # сериализатор для списка постов и для поля author используем UserShortSerializer
    author = UserShortSerializer()
    body = SerializerMethodField()

    class Meta:
        model = Post
        fields = ( "id", "author", "title", "body",
                   "created_at",
        )

    def get_body(self, obj) -> str:
        if len(obj.body) > 128:
            return obj.body[:125] + "..."
        return obj.body


class PostRetrieveSerializer(ModelSerializer):
    # сериализатор для получения полной информации о публикации по ID.
    author = UserShortSerializer()
    my_reaction = SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "title",
            "body",
            "my_reaction",
            "created_at",
        )
    
    def get_my_reaction(self, obj) -> str:
        reaction = self.context["request"].user.reactions.filter(post=obj).last()
        return reaction.value if reaction else ""


class PostCreateUpdateSerializer(ModelSerializer):
    # сериализатор - для создания и обновления поста
    author = HiddenField(
        default = CurrentUserDefault(),
    )
    
    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "title",
            "body",
        )



class UserRegistrationSerializer(ModelSerializer):
    class Meta:
        # с какой моделью будет работать наш сериализатор.
        model = User
        # поля сериализатора
        fields = [ 
            "username",
            "password",
            "email",
            "first_name",
            "last_name",
        ]

    def create(self, validated_data):
        """
        метод create, который отвечает за создание объектов модели

        Наш сериализатор достает из модели ее поля и их типы, затем в соответствии с их типами валидирует данные, полученные из запроса. 
        Если данные верны, то вызвает метод create и передает ему их в качестве аргумента validated_data.
        нам достаточно определить такой сериализатор и он сам будет знать, как валидировать поля тела запроса для создания объекта.
        """
        user = User.objects.create(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user
    

class UserListSerializer(ModelSerializer):
    is_friend = SerializerMethodField()
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "is_friend")
    
    def get_is_friend(self, obj) -> bool:
        current_user = self.context["request"].user
        return current_user in obj.friends.all()


class NestedPostListSerializer(ModelSerializer):
    class Meta:
        model = Post
        # Поле "author" не добавляем намеренно, потому что сам сериализатор будет использоваться, как вложенный в сериализатор 
        # пользователя, в котором будет вся информация об авторе.
        fields = (
            "id",
            "title",
            "body",
            "created_at",
        )


class UserRetrieveSerializer(ModelSerializer):
    is_friend = SerializerMethodField()
    friend_count = SerializerMethodField()
    posts = NestedPostListSerializer(many=True)

    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "email",
                  "is_friend", "friend_count", "posts" ) # сериализатор сам обратится по имени posts и достанет все публикации пользователя.
        
    def get_is_friend(self, obj) -> bool:
        return obj in self.context["request"].user.friends.all()
    
    def get_friend_count(self, obj) -> int:
        return obj.friends.count()



class ReactionSerializer(ModelSerializer):
    author = HiddenField(
        default=CurrentUserDefault(),
    )
    class Meta:
        model = Reaction
        fields = (
            "id", "author", "post", "value",
        )

    def create(self, validated_data):
        reaction = Reaction.objects.filter(
            author=validated_data["author"],
            post=validated_data["post"],
        ).last()
        
        if not reaction:
            return Reaction.objects.create(**validated_data)
        if reaction.value == validated_data["value"]:
            reaction.value = None
        else:
            reaction.value = validated_data["value"]
        reaction.save()
        return reaction
    

class ChatSerializer(ModelSerializer):
    user_1 = HiddenField(
        default=CurrentUserDefault(),
    )

    class Meta:
        model = Chat
        fields = ("id", "user_1", "user_2")
    
    def create(self, validated_data):
        request_user = validated_data["user_1"]
        second_user = validated_data["user_2"]

        chat = Chat.objects.filter(
            Q(user_1=request_user, user_2=second_user)
            | Q(user_1=second_user, user_2=request_user)
        ).first()
        if not chat:
            chat = Chat.objects.create(
                user_1=request_user,
                user_2=second_user,
            )

        return chat

    def to_representation(self, obj):
        """
    Итак, наша логика будет такой: в поле user_2 возвращаем айди первого пользователя, 
    если второй равен текущему (тому, который сделал запрос). Иначе возвращаем айди второго.


    Метод to_representation
    В нем мы можем для какого-либо поля определить иную логику, которая будет выполняться при чтении.
    То, как сериализатор обрабатывает переданные в запросе данные, называется "записью", т.к. сериализатор после этого записывает данные в БД.
    А то, как после этого сериализатор отдает данные в ответе на запрос, называется чтением. 
    Так вот, процесс записи мы оставляем, как есть, и меняем логику чтения.

        """
        representation = super().to_representation(obj)
        representation["user_2"] = (
            obj.user_1.pk
            if obj.user_2 == self.context["request"].user
            else obj.user_2.pk
        )
        return representation
    

class MessageListSerializer(ModelSerializer):
    message_author = CharField() #В модели Message нет поля "message_author". Оно будет браться из кверисета сообщений.
    class Meta:
        model = Message
        fields = ( "id", "content", "message_author", "created_at")


class ChatListSerializer(ModelSerializer):
    companion_name = SerializerMethodField()
    last_message_content = SerializerMethodField()
    last_message_datetime = DateTimeField()

    class Meta:
        model = Chat
        fields = (
            "id",
            "companion_name",
            "last_message_content",
            "last_message_datetime",
        )

    def get_last_message_content(self, obj) -> str:
        return obj.last_message_content

    def get_companion_name(self, obj) -> str:
        companion = obj.user_1 if obj.user_2 == self.context["request"].user else obj.user_2
        return f"{companion.first_name} {companion.last_name}"
    

class MessageSerializer(ModelSerializer):
    """
    отправка сообщений и их удаление.
    """
    author = HiddenField(
        default=CurrentUserDefault()
    )
    def validate(self, attrs):
        chat = attrs["chat"]
        author = attrs["author"]
        if chat.user_1 != author and chat.user_2 != author:
            raise ValidationError("Вы не являетесь участником этого чата.")
        return super().validate(attrs)

    class Meta:
        model = Message
        fields = ("id", "author", "content", "chat", "created_at")