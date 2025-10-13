# isort: skip_file
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from foodgram.constants import MIN_AMOUNT, MIN_COOKING_TIME
from foodgram.models import (
    Account, IngredientAmount, Ingredients, Recipes, Tag
)
from foodgram.validators import validate_image

from .constants import (
    DEFAULT_LIMIT, ERROR_INGREDIENT_ARE_REPEATED,
    ERROR_NO_INGREDIENT, ERROR_NO_TAGS,
    ERROR_TAGS_ARE_REPEATED
)


class UserReadSerializer(UserSerializer):
    """Основной сериализатор для чтения данных о пользователе."""

    is_subscribed = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Account
        fields = (*UserSerializer.Meta.fields, 'is_subscribed', 'avatar')
        read_only_fields = fields


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления/удаления аватара."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = Account
        fields = ('avatar',)


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Укороченный рецепт в подписках"""

    class Meta:
        model = Recipes
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class SubscriptionUserSerializer(UserReadSerializer):
    """Сериализатор автора в подписках."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

    class Meta:
        model = Account
        fields = (*UserReadSerializer.Meta.fields, 'recipes', 'recipes_count')
        read_only_fields = fields

    def get_recipes(self, user_obj):
        return ShortRecipeSerializer(
            user_obj.recipes.all()[:int(
                self.context.get('request').GET.get(
                    'recipes_limit', self.context.get(
                        'recipes_limit', DEFAULT_LIMIT
                    )))],
            many=True,
            context=self.context
        ).data


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализер для продуктов."""

    class Meta:
        model = Ingredients
        fields = ('id', 'name', 'measurement_unit')


class ReadIngredientAmountSerializer(serializers.ModelSerializer):
    """Отображение продуктов в рецепте (чтение)."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class AddIngredientSerializer(serializers.ModelSerializer):
    """Используется при создании/редактировании рецепта."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredients.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField(min_value=MIN_AMOUNT)

    class Meta:
        model = IngredientAmount
        fields = ('id', 'amount')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class ReadRecipeSerializer(serializers.ModelSerializer):
    """Полный сериализатор рецепта."""

    author = UserReadSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = ReadIngredientAmountSerializer(
        source='ingredient_amounts',
        many=True,
        read_only=True)
    is_favorited = serializers.BooleanField(
        default=False,
        read_only=True
    )
    is_in_shopping_cart = serializers.BooleanField(
        default=False,
        read_only=True
    )

    class Meta:
        model = Recipes
        fields = (
            'id',
            'author',
            'name',
            'text',
            'cooking_time',
            'image',
            'tags',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
        )
        read_only_fields = fields


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Создание и редактирование рецепта."""

    image = Base64ImageField(
        required=True,
        allow_null=False,
        validators=(validate_image,)
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    ingredients = AddIngredientSerializer(many=True, required=True)
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        required=True
    )

    class Meta:
        model = Recipes
        fields = (
            'id',
            'name',
            'text',
            'cooking_time',
            'image',
            'tags',
            'ingredients'
        )

    def _get_duplicates(self, items):
        """Возвращает список дубликатов из последовательности."""
        return [item for item in set(items) if items.count(item) > 1]

    def validate(self, data):
        tags = data.get('tags')
        ingredients = data.get('ingredients') or []
        if not tags:
            raise serializers.ValidationError({'tags': ERROR_NO_TAGS})
        if (tag_duplicates := self._get_duplicates(tags)):
            raise serializers.ValidationError({
                'tags': ERROR_TAGS_ARE_REPEATED.format(tag_duplicates)
            })
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients':
                ERROR_NO_INGREDIENT
            })
        if (ingredient_duplicates := self._get_duplicates(
                [item['ingredient'] for item in ingredients])):
            raise serializers.ValidationError({
                'ingredients': ERROR_INGREDIENT_ARE_REPEATED.format(
                    ingredient_duplicates
                )
            })
        return data

    def create_ingredients(self, recipe, ingredients):
        IngredientAmount.objects.bulk_create(
            IngredientAmount(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            ) for item in ingredients
        )

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        instance.tags.set(tags)
        instance.ingredient_amounts.all().delete()
        self.create_ingredients(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return ReadRecipeSerializer(instance, context=self.context).data
