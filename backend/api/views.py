# isort: skip_file
from datetime import datetime

from django.db.models import Count, Exists, OuterRef, Prefetch, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from foodgram.models import (
    Account, Favorite, IngredientAmount, Ingredients,
    Recipes, ShoppingCart, Subscription, Tag
)

from .constants import (
    ERROR_ALREADY_SIGNED, ERROR_AVATAR_PUT,
    ERROR_SUBSCRIE_TO_YOURSELF, FILE_NAME_SHOPPING_CART,
    MONTHS
)
from .filters import IngredientFilter, RecipeTagFilter
from .pagination import StandardPagination
from .serializers import (
    IngredientSerializer, ReadRecipeSerializer,
    RecipeCreateUpdateSerializer, ShortRecipeSerializer,
    SubscriptionUserSerializer, TagSerializer,
    UserAvatarSerializer, UserReadSerializer
)


def generate_shopping_list(user):
    """Формирует текст списка покупок с рецептами."""

    now = datetime.now()
    ingredients = (
        IngredientAmount.objects.filter(
            recipe__shoppingcarts__user=user
        )
        .values(
            'ingredient__name',
            'ingredient__measurement_unit'
        )
        .annotate(total_amount=Sum('amount'))
        .order_by('ingredient__name')
    )
    recipes = (
        Recipes.objects.filter(shoppingcarts__user=user)
        .order_by('name')
    )
    context = {
        'user': user,
        'date': f'{now.day} {MONTHS[now.month]} {now.year}',
        'ingredients': enumerate(ingredients, start=1),
        'recipes': recipes,
    }
    return render_to_string('recipes/shopping_list.txt', context)


class UserViewSet(DjoserUserViewSet):
    """Вьюсет для работы с пользователями и их аватарми."""

    queryset = Account.objects.all()
    serializer_class = UserReadSerializer
    pagination_class = StandardPagination

    @action(
        detail=False, methods=['get'],
        permission_classes=(IsAuthenticated,),
        url_path='me'
    )
    def me(self, request):
        """Информация о текущем пользователе — вызывает базовый метод."""
        return super().me(request)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar'
    )
    def avatar(self, request):
        """Добавление или удаление аватара текущего пользователя."""
        user = request.user
        if request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = UserAvatarSerializer(
            user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if 'avatar' not in request.data:
            raise ValidationError({'avatar': [ERROR_AVATAR_PUT]})
        return Response({'avatar': user.avatar.url}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        """
        Возвращает список авторов, на которых подписан текущий пользователь.
        """
        user = request.user
        queryset = self._get_subscriptions_queryset(user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionUserSerializer(page, many=True, context={
            'request': request,
        })
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        Переопределяем retrieve, чтобы корректно отображалось
        состоянии подписки на страницах пользователей
        """
        user = request.user
        author = self.get_object()
        if user.is_authenticated:
            author.is_subscribed = Subscription.objects.filter(
                user=user,
                author=author
            ).exists()
        serializer = self.get_serializer(author)
        return Response(serializer.data)

    def _get_subscriptions_queryset(self, user, recipes_limit=None):
        """Строит queryset подписок с аннотациями и prefetch рецептов."""
        queryset = Account.objects.filter(authors__user=user).annotate(
            is_subscribed=Exists(
                Subscription.objects.filter(user=user, author=OuterRef('id'))
            ),
            recipes_count=Count('recipes')
        )
        return queryset.prefetch_related(Prefetch(
            'recipes',
            queryset=Recipes.objects.all()
        ))

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
    )
    def subscribe(self, request, id=None):
        """Подписаться или отписаться."""
        user = request.user
        if request.method == 'DELETE':
            get_object_or_404(
                Subscription,
                user=user,
                author_id=id
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        author = self.get_object()
        if user == author:
            raise ValidationError({'errors': ERROR_SUBSCRIE_TO_YOURSELF})
        subscription, created = Subscription.objects.get_or_create(
            user=user,
            author=author
        )
        if not created:
            raise ValidationError({
                'errors': ERROR_ALREADY_SIGNED.format(
                    subscription.author.username
                )
            })
        return Response(
            SubscriptionUserSerializer(
                author,
                context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = (filters.SearchFilter,)
    permission_classes = (AllowAny,)
    search_fields = ('name', 'slug',)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для продуктов."""

    queryset = Ingredients.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = (IngredientFilter,)
    filterset_class = IngredientFilter
    search_fields = ('name',)
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для полной работы с рецептами."""

    queryset = Recipes.objects.all()
    serializer_class = ReadRecipeSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = RecipeTagFilter
    pagination_class = StandardPagination
    search_fields = ('name', 'text',)

    def get_queryset(self):
        """
        Возвращаем queryset рецептов; если пользователь аутентифицирован,
        аннотируем флагами is_favorited и is_in_shopping_cart, чтобы
        сериализатор корректно отдавал True/False.
        """
        qs = Recipes.objects.all().select_related('author').prefetch_related(
            Prefetch('tags'),
            Prefetch(
                'ingredient_amounts',
                queryset=IngredientAmount.objects.select_related('ingredient'))
        )
        user = self.request.user
        if user and user.is_authenticated:
            qs = qs.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=user,
                        recipe_id=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user,
                        recipe_id=OuterRef('pk'))
                )
            )
        return qs

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return ReadRecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        """Возвращает абсолютную короткую ссылку на рецепт."""
        return Response(
            {'short-link':
             request.build_absolute_uri(reverse(
                 'recipe-short-link',
                 args=[pk]))}
        )

    def _manage_recipe_list(self, request, pk, model):
        """Общий метод для добавления/удаления избранного и списка покупок."""
        user = request.user
        if request.method == 'DELETE':
            get_object_or_404(model, user=user, recipe__pk=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        recipe = get_object_or_404(Recipes, pk=pk)
        _, created = model.objects.get_or_create(
            user=user,
            recipe=recipe
        )
        if not created:
            raise ValidationError({
                'errors':
                f'Рецепт{recipe.name} уже добавлен в'
                f'{model._meta.verbose_name.lower()}'
            })
        return Response(
            ShortRecipeSerializer(
                recipe,
                context=self.get_serializer_context()
            ).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def favorite(self, request, pk=None):
        return self._manage_recipe_list(request, pk, Favorite)

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        return self._manage_recipe_list(request, pk, ShoppingCart)

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        return FileResponse(
            generate_shopping_list(request.user),
            content_type='text/plain;',
            as_attachment=True,
            filename=FILE_NAME_SHOPPING_CART,
        )
