from django.contrib import admin
from django.contrib.auth.models import Group

from rangefilter.filters import DateRangeFilter
from django_admin_listfilter_dropdown.filters import ChoiceDropdownFilter

from general.filters import AuthorFilter, PostFilter
from general.models import (
    Post,
    User,
    Comment,
    Reaction,
)



admin.site.unregister(Group)



@admin.register(User)
class UserModelAdmin(admin.ModelAdmin):
    list_display = ( #Это поле должно содержать список или кортеж из имен полей модели, которые надо вывести в таблице.
        "id",
        "first_name",
        "last_name",
        "username",
        "email",
        "is_staff",
        "is_superuser",
        "is_active",
        "date_joined",
    )

    readonly_fields = (
        "date_joined",
        "last_login",
    )   

    fieldsets = ( 
        # Группировка полей на странице создания/редактирования
        # поле "fields", которое хранит кортеж или список с названиями полей модели
        # поле classes, которое хранит кортеж или список с названиями классов стилей.

        # нельзя задавать одновременно fieldsets и fields (страница созд/редакт пользоват), необходимо указать 1-е или 2-е.
    (
        "Личные данные", {
            "fields": (
                "first_name",
                "last_name",
                "email",
            )
        }
    ),
    (
        "Учетные данные", {
            "fields": (
                "username",
                "password",
            )
        }
    ),
    (
        "Статусы", {
            "classes": (
                "collapse",
            ),
            "fields": (
                "is_staff",
                "is_superuser",
                "is_active",
            )
        }
    ),
    (
        None, {
            "fields": (
                "friends",
            )
        }
    ),
    (
        "Даты", {
            "fields": (
                "date_joined",
                "last_login",
            )
        }
    )

)
    
    search_fields = ( # Поиск по фильтрам
        "id",
        "username",
        "email",
    )

    list_filter = ( #  справа от таблицы пользователей вы увидите фильтры по этим полям
    "is_staff",
    "is_superuser",
    "is_active",
    ("data_joined", DateRangeFilter) 
    # мы можем прописывать или выбирать начальную и конечную даты и получать пользователей, зарегистрировавшихся в этом промежутке времени.
)


@admin.register(Post)
class PostModelAdmin(admin.ModelAdmin):
    list_display = (
        "id", 
        "author", 
        "title", 
        "get_body",
        "created_at")
    
    fields = (
        "author",
        "title",
        "body",
        "created_at",
    )

    readonly_fields = ( "created_at", )

    search_fields = (
    "id",
    "title",
    )

    list_filter = (
        AuthorFilter,
        ("created_at", DateRangeFilter),
    )

    def get_queryset(self, request):
        """ 
        под капотом выполнится два запроса: 1) получение всех постов 2) получение всех комментариев к этим постам 
        Метод prefetch_related используется, когда мы для объектов хотим получать набор связанных данных.

        """
        return super().get_queryset(request).prefetch_related("comments")


    # Теперь пользователи и посты не будут подгружаться сразу все, а порциями
    # Нам также нужно убедиться, что в UserModelAdmin и PostModelAdmin определены search_fields
    # autocomplete_fields = ("author","post",)


    def get_body(self, obj): # obj - это пост
        max_length = 64
        if len(obj.body) > max_length:
            return obj.body[:61] + "..."
        else:
            return obj.body
    def get_comment_count(self, obj):
        return obj.comments.count()
    
    get_body.short_description = "body"




@admin.register(Comment)
class CommentModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "post",
        "body",
        "created_at",
    )

    list_display_links = (
        "id",
        "body",
    )

    fields = (
        "author",
        "post",
        "body",
        "created_at",
    )

    readonly_fields = ( "created_at", )

    search_fields = (
        "author__username",
        "post__title",
    )

    list_filter = (
        PostFilter,
        AuthorFilter,
    )

# После перезапуска админки мы увидим, что поле автора стало числовым, а рядом появился значок поиска.
# Этот способ тоже избавляет нас от предварительной загрузки всех пользователей, поэтому страница откроется быстро. 
    raw_id_fields = (
        'author',
    )

@admin.register(Reaction)
class ReactionModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "post",
        "value",
    )
    list_filter = (
    PostFilter,
    AuthorFilter,
    ("value", ChoiceDropdownFilter), # Теперь фильтр будет занимать немного пространства, а значения будут "спрятаны" в выпадающем списке.
)
