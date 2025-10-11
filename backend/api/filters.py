import django_filters
from django_filters import rest_framework as filters

from foodgram.models import Ingredients, Recipes, Tag


class RecipeTagFilter(filters.FilterSet):
    """Фильтры для рецептов — по тегам, автору избранному и корзине."""

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    author = django_filters.NumberFilter(field_name='author')
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipes
        fields = ('tags', 'is_favorited', 'is_in_shopping_cart')

    def _param_is_true(self, val):
        """Приводим значение параметра к булеву."""
        if isinstance(val, bool):
            return val
        if val is None:
            return False
        return str(val).lower() in ('1', 'true', 't', 'yes')

    def filter_is_favorited(self, favorited_queryset, name, value):
        user = self.request.user
        if self._param_is_true(value):
            if user.is_authenticated:
                return favorited_queryset.filter(
                    favorites__user=user
                ).distinct()
            return favorited_queryset.none()
        return favorited_queryset

    def filter_is_in_shopping_cart(self, shopping_cart_queryset, name, value):
        user = self.request.user
        if self._param_is_true(value):
            if user.is_authenticated:
                return shopping_cart_queryset.filter(
                    shoppingcart__user=user
                ).distinct()
            return shopping_cart_queryset.none()
        return shopping_cart_queryset


class IngredientFilter(django_filters.FilterSet):
    """Фильтр для ингредиентов по названию (начало слова)."""
    name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
    )

    class Meta:
        model = Ingredients
        fields = ['name']
