from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count

from foodgram.models import (Favorite, IngredientAmount, Ingredients, Recipes,
                             ShoppingCart, Tag)

from .models import Account, Subscription


@admin.register(Account)
class AccountAdmin(UserAdmin):
    """Кастомизация админ-панели для модели пользователей."""

    search_fields = ('email', 'username')
    list_filter = ('email', 'username')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админ-панель для модели подписок."""

    list_display = ('user', 'author')
    search_fields = ('user__username', 'author__username')


@admin.register(Ingredients)
class IngredientsAdmin(admin.ModelAdmin):
    """Настройка админки для модели ингредиентов."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Настройка админки для модели тегов."""

    list_display = ('name', 'slug')
    search_fields = ('name',)


class IngredientAmountInline(admin.TabularInline):
    """Позволяет редактировать ингредиенты прямо на странице рецепта."""

    model = IngredientAmount
    extra = 1
    min_num = 1


@admin.register(Recipes)
class RecipesAdmin(admin.ModelAdmin):
    """Настройка админки для модели рецептов."""

    list_display = ('name', 'author')
    readonly_fields = ('favorites_count',)
    search_fields = ('name', 'author__username')
    list_filter = ('author', 'name', 'tags')
    inlines = (IngredientAmountInline,)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(fav_count=Count('favorited_by'))
        return queryset

    def favorites_count(self, obj):
        """Выводит общее число добавлений этого рецепта в избранное."""
        return obj.fav_count

    favorites_count.short_description = 'Число добавлений в избранное'
    favorites_count.admin_order_field = 'fav_count'


admin.site.register(Favorite)
admin.site.register(ShoppingCart)
