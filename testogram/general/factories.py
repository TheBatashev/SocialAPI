import factory
from factory.django import DjangoModelFactory
from general.models import User, Post, Comment, Reaction, Chat, Message


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker("user_name")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    is_staff = True


class PostFactory(DjangoModelFactory):
    class Meta:
        model = Post
    
    author = factory.SubFactory(UserFactory)
    # SubFactory. Как он работает?
    # Этот класс позволяет при генерации публикации сгенерировать сначала пользователя и указать его в качестве автора поста

    title = factory.Faker("word")
    body = factory.Faker("text")

class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment
    
    body = factory.Faker("text")
    author = factory.SubFactory(UserFactory)
    post = factory.SubFactory(PostFactory)

class ReactionFactory(DjangoModelFactory):
    class Meta:
        model = Reaction

    value = Reaction.Values.SMILE
    author = factory.SubFactory(UserFactory)
    post = factory.SubFactory(PostFactory)


class ChatFactory(DjangoModelFactory):
    class Meta:
        model = Chat

    user_1 = factory.SubFactory(UserFactory)
    user_2 = factory.SubFactory(UserFactory)


class MessageFactory(DjangoModelFactory):
    class Meta:
        model = Message
    
    content = factory.Faker("text")
    author = factory.SubFactory(UserFactory)
    chat = factory.LazyAttribute(lambda obj: ChatFactory(user_1=obj.author))
    # LazyAttribute. Он позволяет определить сложную логику для полей при создании экземпляра класса.
    # В нашем случае он для создания чата в качестве user_1 передает автора сообщения.
