from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count, Max, Min
from django.utils.safestring import mark_safe

from .models import (Account, Favorite, IngredientAmount, Ingredients, Recipes,
                     ShoppingCart, Subscription, Tag)


class RelatedExistenceFilter(admin.SimpleListFilter):
    """Абстрактный базовый класс фильтрации по наличию связанных объектов."""
    title = ''
    parameter_name = ''
    field_name = ''
    LOOKUP_CHOICES = (('yes', 'Да'), ('no', 'Нет'),)

    def lookups(self, request, model_admin):
        return self.LOOKUP_CHOICES

    def queryset(self, request, queryset):
        """Фильтрует queryset на основе наличия связанных объектов."""
        if not self.field_name:
            raise NotImplementedError(
                'Не хватает атребута field_name'
            )
        lookup = f'{self.field_name}__isnull'
        if self.value() == 'yes':
            return queryset.filter(**{lookup: False}).distinct()
        if self.value() == 'no':
            return queryset.filter(**{lookup: True}).distinct()
        return queryset


class HasRecipesFilter(RelatedExistenceFilter):
    title = 'Наличие рецептов'
    parameter_name = 'has_recipes'
    field_name = 'recipes'


class HasSubscriptionsFilter(RelatedExistenceFilter):
    title = 'Наличие подписок'
    parameter_name = 'has_subscriptions'
    field_name = 'subscriptions'


class HasSubscribersFilter(RelatedExistenceFilter):
    title = 'Наличие подписчиков'
    parameter_name = 'has_subscribers'
    field_name = 'authors'


class InRecipeFilter(RelatedExistenceFilter):
    title = 'Используется в рецептах'
    parameter_name = 'in_recipe'
    field_name = 'recipes'


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
        HasRecipesFilter,
        HasSubscriptionsFilter,
        HasSubscribersFilter,
    )

    @admin.display(description='ФИО')
    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'

    @admin.display(description='Аватар',)
    @mark_safe
    def avatar_display(self, user):
        if user.avatar:
            return f'<img src="{user.avatar.url}" width="50" height="50" />'
        return '-'

    @admin.display(description='Рецепты')
    def recipes_count(self, user):
        return user.recipes.count()

    @admin.display(description='Подписки')
    def subscriptions_count(self, user):
        return user.subscriptions.count()

    @admin.display(description='Подписчики')
    def subscribers_count(self, user):
        return user.authors.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админ-панель для модели подписок."""

    list_display = ('user', 'author')
    search_fields = ('user__username', 'author__username')


class RelatedRecipesAdminMixin:
    """Добавляет отображение числа рецептов для связанных моделей."""

    list_display_with_recipes_count = ('recipes_count',)

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
        *RelatedRecipesAdminMixin.list_display_with_recipes_count,
    )
    search_fields = ('name',)
    list_filter = ('measurement_unit', InRecipeFilter,)


class IngredientAmountInline(admin.TabularInline):
    """Позволяет редактировать продуктов прямо на странице рецепта."""

    model = IngredientAmount
    extra = 1
    min_num = 1


@admin.register(Tag)
class TagAdmin(RelatedRecipesAdminMixin, admin.ModelAdmin):
    """Настройка админки для модели тегов."""

    list_display = (
        'name',
        'slug',
        *RelatedRecipesAdminMixin.list_display_with_recipes_count,
    )
    search_fields = ('name', 'slug')


class CookingTimeFilter(admin.SimpleListFilter):
    """Фильтр рецептов по длительности готовки."""

    title = 'Время готовки'
    parameter_name = 'cooking_time_group'
    SHORT_LABEL = 'short'
    MEDIUM_LABEL = 'medium'
    LONG_LABEL = 'long'

    def lookups(self, request, model_admin):
        recipes = model_admin.model.objects.all()
        if recipes.values('cooking_time').distinct().count() < 3:
            return []
        aggregates = recipes.aggregate(
            min_time=Min('cooking_time'), max_time=Max('cooking_time')
        )
        min_time = aggregates.get('min_time')
        max_time = aggregates.get('max_time')
        time_range = max_time - min_time
        if time_range <= 0:
            return []
        short_border = min_time + (time_range) // 3
        medium_border = min_time + 2 * (time_range) // 3
        self.thresholds = {
            self.SHORT_LABEL: (min_time, short_border),
            self.MEDIUM_LABEL: (short_border, medium_border),
            self.LONG_LABEL: (medium_border, max_time),
        }
        return [
            (self.SHORT_LABEL, f'Быстрые (< {short_border} мин)'),
            (self.MEDIUM_LABEL, f'Средние ({short_border}–'
             f'{int(medium_border)} мин)'),
            (self.LONG_LABEL, f'Долгие (> {medium_border} мин)'),
        ]

    def queryset(self, request, recipes):
        value = self.value()
        if value in self.thresholds:
            return recipes.filter(cooking_time__range=self.thresholds[value])
        return recipes


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
    list_filter = ('author', 'tags', CookingTimeFilter)
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
    @mark_safe
    def ingredients_list(self, recipe):
        """
        Возвращает список продуктов с количеством и единицами измерения.
        """
        return '<br>'.join(
            f'{ing.ingredient.name} — {ing.amount}'
            f'{ing.ingredient.measurement_unit}'
            for ing in recipe.ingredient_amounts.all()
        )

    @admin.display(description='Теги')
    @mark_safe
    def tags_list(self, recipe):
        """Возвращает список тегов рецепта."""
        return '<br>'.join(tag.name for tag in recipe.tags.all())

    @admin.display(description='Изображение')
    @mark_safe
    def recipe_image(self, recipe):
        """Показывает миниатюру изображения рецепта."""
        if recipe.image:
            return f'<img src="{recipe.image.url}" width="70" height="70" />'
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
