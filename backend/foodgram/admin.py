from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from django.utils.safestring import mark_safe

from .models import (Account, Favorite, IngredientAmount, Ingredients, Recipes,
                     ShoppingCart, Subscription, Tag)


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
    list_filter = ('email', 'username')

    @admin.display(description='ФИО')
    def full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'

    @admin.display(description='Аватар')
    def avatar_display(self, obj):
        if obj.avatar:
            return mark_safe(
                f'<img src="{obj.avatar.url}" width="50" height="50" />'
            )
        return '-'

    @admin.display(description='Количество рецептов')
    def recipes_count(self, obj):
        return obj.recipes.count()

    @admin.display(description='Количество подписок')
    def subscriptions_count(self, obj):
        return obj.subscriptions.count()

    @admin.display(description='Количество подписчиков')
    def subscribers_count(self, obj):
        return obj.authors.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админ-панель для модели подписок."""

    list_display = ('user', 'author')
    search_fields = ('user__username', 'author__username')


class RelatedRecipesAdminMixin:
    """Добавляет отображение числа рецептов для связанных моделей."""

    @admin.display(description='Число рецептов', ordering='recipes_count')
    def recipes_count(self, obj):
        return obj.recipes_count

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(recipes_count=Count('recipes', distinct=True))


@admin.register(Ingredients)
class IngredientsAdmin(RelatedRecipesAdminMixin, admin.ModelAdmin):
    """Настройка админки для модели ингредиентов."""

    list_display = (
        'name',
        'measurement_unit',
        'recipes_count',
    )
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


class IngredientAmountInline(admin.TabularInline):
    """Позволяет редактировать ингредиенты прямо на странице рецепта."""

    model = IngredientAmount
    extra = 1
    min_num = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Настройка админки для модели тегов."""

    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')


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
    list_filter = ('author', 'cooking_time')
    inlines = (IngredientAmountInline,)

    def get_queryset(self, request):
        """Аннотируем queryset, чтобы считать избранное."""
        queryset = super().get_queryset(request)
        return queryset.annotate(fav_count=Count('favorited_by'))

    @admin.display(description='В избранном', ordering='fav_count')
    def favorites_count(self, recipe):
        """Показывает, сколько раз рецепт был добавлен в избранное."""
        return recipe.fav_count

    @admin.display(description='Ингредиенты')
    def ingredients_list(self, obj):
        """
        Возвращает список ингредиентов с количеством и единицами измерения.
        """
        ingredients = obj.ingredients.all()
        result = '<br>'.join(
            f'{ing.name} — {ing.ingredientamount.amount}{ing.measurement_unit}'
            for ing in ingredients
        )
        return mark_safe(result) if ingredients else '-'

    @admin.display(description='Теги')
    def tags_list(self, obj):
        """Возвращает список тегов рецепта."""
        tags = obj.tags.all()
        return ', '.join(tag.name for tag in tags) if tags else '-'

    @admin.display(description='Изображение')
    def recipe_image(self, obj):
        """Показывает миниатюру изображения рецепта."""
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="70" height="70" />'
            )
        return '-'

    def get_list_filter(self, request):
        """Добавляем кастомный фильтр по времени готовки."""
        filters = super().get_list_filter(request)
        return list(filters) + [CookingTimeFilter]
    favorites_count.admin_order_field = 'fav_count'


class CookingTimeFilter(admin.SimpleListFilter):
    """Фильтр рецептов по длительности готовки."""

    title = 'Время готовки'
    parameter_name = 'cooking_time_group'

    def lookups(self, request, model_admin):
        return [
            ('short', 'Быстрые (< 20 мин)'),
            ('medium', 'Средние (20–60 мин)'),
            ('long', 'Долгие (> 60 мин)'),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value == 'short':
            return queryset.filter(cooking_time__lt=20)
        if value == 'medium':
            return queryset.filter(cooking_time__gte=20, cooking_time__lte=60)
        if value == 'long':
            return queryset.filter(cooking_time__gt=60)
        return queryset


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админ-панель для модели избранных рецептов."""

    list_display = ('id', 'user', 'recipe', 'recipe_author', 'recipe_name')
    search_fields = ('user__username', 'recipe__name')

    @admin.display(description='Автор рецепта')
    def recipe_author(self, favorite):
        return favorite.recipe.author

    @admin.display(description='Название рецепта')
    def recipe_name(self, favorite):
        return favorite.recipe.name


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админ-панель для модели списка покупок."""

    list_display = ('id', 'user', 'recipe', 'recipe_author', 'recipe_name')
    search_fields = ('user__username', 'recipe__name')

    @admin.display(description='Автор рецепта')
    def recipe_author(self, cart_item):
        return cart_item.recipe.author

    @admin.display(description='Название рецепта')
    def recipe_name(self, cart_item):
        return cart_item.recipe.name
