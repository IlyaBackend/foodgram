from datetime import datetime
from io import BytesIO

from django.db.models import Count, Exists, OuterRef, Prefetch, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from foodgram.models import (Account, Favorite, IngredientAmount, Ingredients,
                             Recipes, ShoppingCart, Subscription, Tag)

from .constants import (ERROR_ALREADY_SIGNED, ERROR_AVATAR_PUT,
                        ERROR_RECIPE_IN_FAVORITES,
                        ERROR_RECIPE_IN_SHOPPING_CART,
                        ERROR_RECIPE_NOT_IN_FAVORITES,
                        ERROR_RECIPE_NOT_IN_SHOPPING_CART,
                        ERROR_SUBSCRIE_TO_YOURSELF,
                        ERROR_YOU_ARE_NOT_SUBSCRIBED, FILE_NAME_SHOPPING_CART)
from .filters import IngredientFilter, RecipeTagFilter
from .pagination import StandardPagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (IngredientSerializer, ReadRecipeSerializer,
                          RecipeCreateUpdateSerializer, ShortRecipeSerializer,
                          SubscriptionUserSerializer, TagSerializer,
                          UserAvatarSerializer, UserReadSerializer)


def generate_shopping_list(user):
    """Формирует текст списка покупок с рецептами."""
    ingredients = (
        IngredientAmount.objects.filter(
            recipe__shoppingcart__user=user
        )
        .values(
            'ingredient__name',
            'ingredient__measurement_unit'
        )
        .annotate(total_amount=Sum('amount'))
        .order_by('ingredient__name')
    )
    recipes = (
        Recipes.objects.filter(shoppingcart__user=user)
        .values('name', 'author__username')
        .order_by('name')
    )
    context = {
        'user': user,
        'date': datetime.now().strftime('%d.%m.%Y'),
        'ingredients': enumerate(ingredients, start=1),
        'recipes': recipes,
    }
    text = render_to_string('recipes/shopping_list.txt', context)
    buffer = BytesIO()
    buffer.write(text.encode('utf-8'))
    buffer.seek(0)
    return buffer


class ActionPermissionClassesMixin:
    """
    Миксин, который позволяет определять разрешения на основе действия
    в словаре 'permission_classes'.
    """

    def get_permissions(self):
        """
        Если permission_classes является словарем, он будет использоваться
        для поиска разрешений по текущему self.action.
        Иначе используется стандартное поведение.
        """
        if isinstance(self.permission_classes, dict):
            permission_classes = self.permission_classes.get(
                self.action,
                self.permission_classes.get('*', [])
            )
            return [permission() for permission in permission_classes]
        return super().get_permissions()


class UserViewSet(ActionPermissionClassesMixin, DjoserUserViewSet):
    """Вьюсет для работы с пользователями и их аватарми."""

    queryset = Account.objects.all()
    serializer_class = UserReadSerializer
    pagination_class = StandardPagination
    permission_classes = {
        'me': [IsAuthenticated],
        'subscriptions': [IsAuthenticated],
        'subscribe': [IsAuthenticated],
        'avatar': [IsAuthenticated],
        '*': [AllowAny],
    }

    def perform_create(self, serializer):
        """Создание пользователя (perform-версия create)."""
        serializer.save()

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """Информация о текущем пользователе — вызывает базовый метод."""
        return super().me(request)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def avatar(self, request):
        """Добавление или удаление аватара текущего пользователя."""
        user = request.user
        serializer = UserAvatarSerializer(
            user, data=request.data, partial=True
        )
        if request.method == 'PUT':
            serializer.is_valid(raise_exception=True)
            serializer.save()
            if 'avatar' not in request.data:
                raise ValidationError({'avatar': [ERROR_AVATAR_PUT]})
            return Response(
                {'avatar': user.avatar.url},
                status=status.HTTP_200_OK
            )
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='subscriptions',)
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

    def _get_subscriptions_queryset(self, user, recipes_limit=None):
        """Строит queryset подписок с аннотациями и prefetch рецептов."""
        if user.is_anonymous:
            return False
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

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe',)
    def subscribe(self, request, id=None):
        """Подписаться или отписаться."""
        user = request.user
        if request.method == 'POST':
            author = self.get_object()
            subscription, created = Subscription.objects.get_or_create(
                user=user,
                author=author
            )
            if not created:
                raise ValidationError({
                    'errors':
                    f'{ERROR_ALREADY_SIGNED} - {subscription}'
                })
            if user == author:
                raise ValidationError({'errors': ERROR_SUBSCRIE_TO_YOURSELF})
            serializer = SubscriptionUserSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        subscription = Subscription.objects.filter(
            user=user,
            author=get_object_or_404(Account, pk=id)
        ).first()
        if not subscription:
            return Response(
                {'errors': ERROR_YOU_ARE_NOT_SUBSCRIBED},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Просмотр тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = (filters.SearchFilter,)
    permission_classes = (AllowAny,)
    search_fields = ('name', 'slug',)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""

    queryset = Ingredients.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = (IngredientFilter,)
    filterset_class = IngredientFilter
    search_fields = ('name',)
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(ActionPermissionClassesMixin, viewsets.ModelViewSet):
    """Вьюсет для полной работы с рецептами."""

    queryset = Recipes.objects.all()
    serializer_class = ReadRecipeSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = RecipeTagFilter
    pagination_class = StandardPagination
    permission_classes = {
        'create': (IsOwnerOrReadOnly, IsAuthenticated,),
        'favorite': (IsOwnerOrReadOnly, IsAuthenticated,),
        'shopping_cart': (IsOwnerOrReadOnly, IsAuthenticated,),
        'download_shopping_cart': (IsOwnerOrReadOnly, IsAuthenticated,),
        'update': (IsOwnerOrReadOnly, IsAuthenticated,),
        'partial_update': (IsOwnerOrReadOnly, IsAuthenticated,),
        'destroy': (IsOwnerOrReadOnly, IsAuthenticated,),
        '*': (AllowAny,),
    }
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
        relative_url = reverse(
            'recipe-short-link',
            kwargs={'short_code': get_object_or_404(
                Recipes.objects.only('short_code'),
                pk=pk
            ).short_code
            }
        )
        short_url = request.build_absolute_uri(relative_url)
        return Response({'short-link': short_url})

    def _manage_recipe_list(self, request, pk, model):
        """Общий метод для добавления/удаления избранного и списка покупок."""
        user = request.user
        if model.__name__ == 'Favorite':
            already_exists_msg = ERROR_RECIPE_IN_FAVORITES
            not_exists_msg = ERROR_RECIPE_NOT_IN_FAVORITES
        elif model.__name__ == 'ShoppingCart':
            already_exists_msg = ERROR_RECIPE_IN_SHOPPING_CART
            not_exists_msg = ERROR_RECIPE_NOT_IN_SHOPPING_CART
        else:
            already_exists_msg = 'Объект уже существует.'
            not_exists_msg = 'Объект не найден.'
        if request.method == 'POST':
            recipe = get_object_or_404(Recipes, pk=pk)
            obj, created = model.objects.get_or_create(
                user=user,
                recipe=recipe
            )
            if not created:
                raise ValidationError({'errors': already_exists_msg})
            return Response(
                ShortRecipeSerializer(
                    recipe,
                    context=self.get_serializer_context()
                ).data,
                status=status.HTTP_201_CREATED
            )
        if not Recipes.objects.filter(pk=pk).exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        if not model.objects.filter(user=user, recipe__pk=pk).exists():
            raise ValidationError({'errors': not_exists_msg})
        get_object_or_404(model, user=user, recipe__pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def favorite(self, request, pk=None):
        return self._manage_recipe_list(request, pk, Favorite)

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        return self._manage_recipe_list(request, pk, ShoppingCart)

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        buffer = generate_shopping_list(request.user)
        return FileResponse(
            buffer,
            content_type='text/plain; charset=utf-8',
            as_attachment=True,
            filename=FILE_NAME_SHOPPING_CART,
        )


class RecipeShortLinkRedirectView(View):
    """
    Контроллер для перенаправления с короткой ссылки
    на полную страницу рецепта.
    """

    def get(self, request, *args, **kwargs):
        """Получаем ссылку """
        short_code = self.kwargs.get('short_code')
        recipe = get_object_or_404(Recipes, short_code=short_code)
        full_url = reverse('recipes-detail', kwargs={'pk': recipe.pk})
        return redirect(full_url)
