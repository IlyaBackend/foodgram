from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count, Max, Min
from django.utils.html import format_html

from .models import (Account, Favorite, IngredientAmount, Ingredients, Recipes,
                     ShoppingCart, Subscription, Tag)


def create_related_existence_filter(field_name, filter_title, param_name):
    """
    Фабрика для создания SimpleListFilter, который проверяет
    наличие связанных объектов (например, есть ли у пользователя рецепты).
    """
    class RelatedExistenceFilter(admin.SimpleListFilter):
        title = filter_title
        parameter_name = param_name

        def lookups(self, request, model_admin):
            return (
                ('yes', 'Да'),
                ('no', 'Нет'),
            )

        def queryset(self, request, queryset):
            lookup = f'{field_name}__isnull'
            if self.value() == 'yes':
                return queryset.filter(**{lookup: False}).distinct()
            if self.value() == 'no':
                return queryset.filter(**{lookup: True}).distinct()
            return queryset

    return RelatedExistenceFilter


@admin.register(Account)
class AccountAdmin(UserAdmin):
    """Кастомизация админ-панели для модели пользователей."""

    list_display = (
        'id',
        'username',
        'full_name',
        'email',
        'avatar_display',
        'recipes_count',
        'subscriptions_count',
        'subscribers_count'
    )
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = (
        create_related_existence_filter(
            'recipes', 'Наличие рецептов', 'has_recipes'
        ),
        create_related_existence_filter(
            'subscriptions', 'Наличие подписок', 'has_subscriptions'
        ),
        create_related_existence_filter(
            'authors', 'Наличие подписчиков', 'has_subscribers'
        ),
    )

    @admin.display(description='ФИО')
    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'

    @admin.display(description='Аватар',)
    def avatar_display(self, user):
        if user.avatar:
            return format_html(
                '<img src="{}" width="50" height="50" />',
                user.avatar.url
            )
        return '-'

    @admin.display(description='Рецепты')
    def recipes_count(self, instance):
        return instance.recipes.count()

    @admin.display(description='Подписоки')
    def subscriptions_count(self, instance):
        return instance.subscriptions.count()

    @admin.display(description='Подписчики')
    def subscribers_count(self, instance):
        return instance.authors.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админ-панель для модели подписок."""

    list_display = ('user', 'author')
    search_fields = ('user__username', 'author__username')


class RelatedRecipesAdminMixin:
    """Добавляет отображение числа рецептов для связанных моделей."""

    @admin.display(description='Рецепты', ordering='recipes_count')
    def recipes_count(self, recipe):
        return recipe.recipes_count

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(recipes_count=Count('recipes', distinct=True))


@admin.register(Ingredients)
class IngredientsAdmin(RelatedRecipesAdminMixin, admin.ModelAdmin):
    """Настройка админки для модели продуктов."""

    list_display = (
        'name',
        'measurement_unit',
        'recipes_count',
    )
    search_fields = ('name',)
    list_filter = (
        'measurement_unit',
        create_related_existence_filter(
            'recipes', 'Используется в рецептах', 'in_recipe'
        ),
    )


class IngredientAmountInline(admin.TabularInline):
    """Позволяет редактировать продуктов прямо на странице рецепта."""

    model = IngredientAmount
    extra = 1
    min_num = 1


@admin.register(Tag)
class TagAdmin(RelatedRecipesAdminMixin, admin.ModelAdmin):
    """Настройка админки для модели тегов."""

    list_display = ('name', 'slug', 'recipes_count')
    search_fields = ('name', 'slug')


class CookingTimeFilter(admin.SimpleListFilter):
    """Фильтр рецептов по длительности готовки."""

    title = 'Время готовки'
    parameter_name = 'cooking_time_group'
    SHORT_LABEL = 'short'
    MEDIUM_LABEL = 'medium'
    LONG_LABEL = 'long'

    def lookups(self, request, model_admin):
        queryset = model_admin.model.objects.all()
        min_time = queryset.aggregate(
            Min('cooking_time')
        )['cooking_time__min'] or 0
        max_time = queryset.aggregate(
            Max('cooking_time')
        )['cooking_time__max'] or 0
        short_border = min_time + (max_time - min_time) / 3
        medium_border = min_time + 2 * (max_time - min_time) / 3
        self.thresholds = {
            self.SHORT_LABEL: (min_time, short_border),
            self.MEDIUM_LABEL: (short_border, medium_border),
            self.LONG_LABEL: (medium_border, max_time),
        }
        return [
            (self.SHORT_LABEL, f'Быстрые (< {int(short_border)} мин)'),
            (self.MEDIUM_LABEL, f'Средние ({int(short_border)}–'
             f'{int(medium_border)} мин)'),
            (self.LONG_LABEL, f'Долгие (> {int(medium_border)} мин)'),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value in getattr(self, 'thresholds', {}):
            start, end = self.thresholds[value]
            return queryset.filter(cooking_time__range=(start, end))
        return queryset


@admin.register(Recipes)
class RecipesAdmin(admin.ModelAdmin):
    """Настройка админки для модели рецептов."""

    list_display = (
        'id', 'name', 'author', 'cooking_time',
        'favorites_count', 'ingredients_list',
        'tags_list', 'recipe_image'
    )
    readonly_fields = ('favorites_count',)
    search_fields = ('name', 'author__username')
    list_filter = ('author', 'cooking_time', CookingTimeFilter)
    inlines = (IngredientAmountInline,)

    def get_queryset(self, request):
        """Аннотируем queryset, чтобы считать избранное."""
        queryset = super().get_queryset(request)
        return queryset.annotate(fav_count=Count('favorite', distinct=True))

    @admin.display(description='В избранном', ordering='-fav_count')
    def favorites_count(self, recipe):
        """Показывает, сколько раз рецепт был добавлен в избранное."""
        return recipe.fav_count

    @admin.display(description='Продукты')
    def ingredients_list(self, recipe):
        """
        Возвращает список продуктов с количеством и единицами измерения.
        """
        return format_html('<br>'.join(
            f'{ing.ingredient.name} — {ing.amount}'
            f'{ing.ingredient.measurement_unit}'
            for ing in recipe.ingredient_amounts.all()
        ))

    @admin.display(description='Теги')
    def tags_list(self, recipe):
        """Возвращает список тегов рецепта."""
        return format_html('<br>'.join(tag.name for tag in recipe.tags.all()))

    @admin.display(description='Изображение')
    def recipe_image(self, recipe):
        """Показывает миниатюру изображения рецепта."""
        if recipe.image:
            return format_html(
                f'<img src="{recipe.image.url}" width="70" height="70" />'
            )
        return '-'


@admin.register(Favorite, ShoppingCart)
class UserRecipeRelationAdmin(admin.ModelAdmin):
    """Админ-панель для модели избранных рецептов и списка покупок."""

    list_display = ('id', 'user', 'recipe', 'recipe_author', 'recipe_name')
    search_fields = ('user__username', 'recipe__name')

    @admin.display(description='Автор рецепта')
    def recipe_author(self, instance):
        return instance.recipe.author

    @admin.display(description='Название рецепта')
    def recipe_name(self, instance):
        return instance.recipe.name
