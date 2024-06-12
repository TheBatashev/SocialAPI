from admin_auto_filters.filters import AutocompleteFilter


class AuthorFilter(AutocompleteFilter):
    title = 'Author' # это название фильтра, которое будет отображаться в админке
    field_name = 'author' #  это поле модели, к которому будет применяться этот фильтр
    # В нашем случае у публикаций есть поле author и фильтровать будем по нему.

class PostFilter(AutocompleteFilter):
    title = 'Post'
    field_name = 'post'