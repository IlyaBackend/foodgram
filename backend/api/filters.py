import django_filters
from django_filters import rest_framework as filters

from foodgram.models import Recipes, Tag


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

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if self._param_is_true(value):
            if user.is_authenticated:
                return queryset.filter(favorited_by__user=user).distinct()
            return queryset.none()
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if self._param_is_true(value):
            if user.is_authenticated:
                return queryset.filter(in_carts__user=user).distinct()
            return queryset.none()
        return queryset
