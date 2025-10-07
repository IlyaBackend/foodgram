from django.db.models import Count, Exists, OuterRef, Prefetch, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Account, Subscription

from backend.constants import (ERROR_ALREADY_SIGNED, ERROR_AVATAR_PUT,
                               ERROR_RECIPE_IN_FAVORITES,
                               ERROR_RECIPE_IN_SHOPPING_CART,
                               ERROR_RECIPE_NOT_IN_FAVORITES,
                               ERROR_RECIPE_NOT_IN_SHOPPING_CART,
                               ERROR_SUBSCRIE_TO_YOURSELF,
                               ERROR_YOU_ARE_NOT_SUBSCRIBED,
                               FILE_NAME_SHOPPING_CART)
from foodgram.models import (Favorite, IngredientAmount, Ingredients, Recipes,
                             ShoppingCart, Tag)

from .filters import RecipeTagFilter
from .pagination import CustomPagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (IngredientSerializer, RecipeCreateUpdateSerializer,
                          RecipeSerializer, SetPasswordSerializer,
                          ShortRecipeSerializer, SubscriptionUserSerializer,
                          TagSerializer, UserAvatarSerializer, UserSerializer,
                          UserSignUpSerializer)


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с пользователями и их аватарми."""

    queryset = Account.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination

    def get_serializer_class(self):
        """
        Выбираем сериализатор в зависимости от действия (action).
        """
        if self.action == 'signup':
            return UserSignUpSerializer
        if self.action == 'set_password':
            return super().get_serializer_class()
        if self.action == 'avatar':
            return UserAvatarSerializer
        return UserSerializer

    def get_queryset(self):
        """Аннотируем поле is_subscribed."""
        queryset = Account.objects.all()
        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_subscribed=Exists(
                    Subscription.objects.filter(
                        user=user, author=OuterRef('pk'))
                )
            )
        return queryset

    def get_permissions(self):
        """Разрешаем?"""
        if self.action in ('signup', 'create'):
            permission_classes = (AllowAny,)
        elif self.action in (
            'set_password',
            'partial_update',
            'update',
            'destroy',
            'avatar',
            'me',
            'subscriptions',
            'subscribe',
        ):
            permission_classes = (IsAuthenticated,)
        else:
            permission_classes = (AllowAny,)
        return [perm() for perm in permission_classes]

    def create(self, request, *args, **kwargs):
        """Регистрация нового пользователя."""
        serializer = UserSignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='me',)
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='set_password')
    def set_password(self, request):
        """Меняем пароль."""
        user = request.user
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def avatar(self, request):
        """Добавление или удаление аватара текущего пользователя."""
        user = request.user
        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(
                    {'avatar': [ERROR_AVATAR_PUT]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = UserAvatarSerializer(
                user, data=request.data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {'avatar': user.avatar.url},
                    status=status.HTTP_200_OK
                )
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='subscriptions',)
    def subscriptions(self, request):
        """
        Возвращает список авторов, на которых подписан текущий пользователь.
        """
        user = request.user
        recipes_limit = self._get_recipes_limit(request)
        queryset = self._get_subscriptions_queryset(user, recipes_limit)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionUserSerializer(page, many=True, context={
            'request': request,
            'recipes_limit': recipes_limit
        })
        return self.get_paginated_response(serializer.data)

    def _get_recipes_limit(self, request):
        """Извлекает recipes_limit из query params."""
        limit_str = request.query_params.get('recipes_limit')
        if limit_str and limit_str.isdigit():
            return int(limit_str)
        return 5

    def _get_subscriptions_queryset(self, user, recipes_limit=None):
        """Строит queryset подписок с аннотациями и prefetch рецептов."""
        if user.is_anonymous:
            return False
        queryset = Account.objects.filter(subscribers__user=user).annotate(
            is_subscribed=Exists(
                Subscription.objects.filter(user=user, author=OuterRef('pk'))
            ),
            recipes_count=Count('recipes')
        )
        return queryset.prefetch_related(Prefetch(
            'recipes',
            queryset=Recipes.objects.all()
        ))

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe',)
    def subscribe(self, request, pk=None):
        """Подписаться или отписаться."""
        user = request.user
        author = self.get_object()
        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': ERROR_SUBSCRIE_TO_YOURSELF},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {'errors': ERROR_ALREADY_SIGNED},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(user=user, author=author)
            serializer = SubscriptionUserSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        deleted = Subscription.objects.filter(
            user=user,
            author=author).delete()
        if not deleted[0]:
            return Response(
                {'errors': ERROR_YOU_ARE_NOT_SUBSCRIBED},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """Просмотр тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_backends = [filters.SearchFilter]
    permission_classes = (AllowAny,)
    search_fields = ['name', 'slug',]
    pagination_class = None


class IngredientViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """Вьюсет для ингредиентов."""

    queryset = Ingredients.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name',]
    permission_classes = (AllowAny,)
    pagination_class = None

    def get_queryset(self):
        """Добавляем фильтрацию по параметру name."""
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для полной работы с рецептами."""

    queryset = Recipes.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = RecipeTagFilter
    pagination_class = CustomPagination
    search_fields = ['name', 'text',]

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
        return RecipeSerializer

    def get_permissions(self):
        """Определяет права доступа в зависимости от действия."""
        if self.action in (
            'create',
            'favorite',
            'shopping_cart',
            'download_shopping_cart'
        ):
            permission_classes = (IsAuthenticated,)
        elif self.action in (
            'update',
            'partial_update',
            'destroy'
        ):
            permission_classes = (IsOwnerOrReadOnly, IsAuthenticated,)
        else:
            permission_classes = (AllowAny,)
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """Переопределяем для правильной работы детального просмотра."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_short_link(self, request, pk=None):
        """Возвращает абсолютную короткую ссылку на рецепт."""
        obj = self.get_object()
        short_code = getattr(obj, 'short_code', pk)
        short_url = request.build_absolute_uri(f'/s/{short_code}')
        return Response({'short-link': short_url})

    def _manage_recipe_list(self, request, pk, model, errors):
        """Общий метод для добавления/удаления избранного и списка покупок."""
        recipe = get_object_or_404(Recipes, pk=pk)
        user = request.user
        instance_exists = model.objects.filter(
            user=user,
            recipe=recipe
        ).exists()
        if request.method == 'POST':
            if instance_exists:
                return Response(
                    {'errors': errors['already_exists']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeSerializer(
                recipe, context=self.get_serializer_context()
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            if not instance_exists:
                return Response(
                    {'errors': errors['not_exists']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def favorite(self, request, pk=None):
        errors = {
            'already_exists': ERROR_RECIPE_IN_FAVORITES,
            'not_exists': ERROR_RECIPE_NOT_IN_FAVORITES
        }
        return self._manage_recipe_list(request, pk, Favorite, errors)

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        errors = {
            'already_exists': ERROR_RECIPE_IN_SHOPPING_CART,
            'not_exists': ERROR_RECIPE_NOT_IN_SHOPPING_CART
        }
        return self._manage_recipe_list(request, pk, ShoppingCart, errors)

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = IngredientAmount.objects.filter(
            recipe__in_carts__user=user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        shopping_list = 'Список покупок для Foodgram:\n\n'
        for item in ingredients:
            shopping_list += (
                f'- {item["ingredient__name"]} '
                f'({item["ingredient__measurement_unit"]}) — '
                f'{item["total_amount"]}\n'
            )

        response = HttpResponse(shopping_list, content_type='text/plain')
        response[
            'Content-Disposition'
        ] = f'attachment; filename={FILE_NAME_SHOPPING_CART}'
        return response
