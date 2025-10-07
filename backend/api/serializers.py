import base64
import uuid

from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from rest_framework import serializers

from backend.constants import (EMAIL_MAX_LENGTH, ERROR_CURRENT_PASSWORD,
                               ERROR_INGREDIENT_ARE_REPEATED,
                               ERROR_NO_INGREDIENT, ERROR_NO_TAGS,
                               ERROR_TAGS_ARE_REPEATED,
                               ERROR_ZERO_INGREDIEN_AMOUNT,
                               FIRST_NAME_MAX_LENGTH, LAST_NAME_MAX_LENGTH,
                               MAX_DIGITS_AMOUNT, MAX_PLACES_AMOUNT,
                               REGULAR_USERNAME, USERNAME_MAX_LENGTH)
from backend.validators import (unique_email_validator,
                                unique_username_validator)
from foodgram.models import IngredientAmount, Ingredients, Recipes, Tag
from users.models import Account


class Base64ImageField(serializers.ImageField):
    """Поле для ImageField: принимает base64, возвращает URL."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=f'{uuid.uuid4()}.{ext}'
            )
        return super().to_internal_value(data)

    def to_representation(self, value):
        """При отдаче данных возвращаем URL вместо base64."""
        if value and hasattr(value, 'url'):
            return value.url
        return None


class UserSignUpSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации нового пользователя."""

    email = serializers.EmailField(
        required=True,
        max_length=EMAIL_MAX_LENGTH,
        validators=(unique_email_validator(),),
    )
    username = serializers.RegexField(
        REGULAR_USERNAME,
        required=True,
        max_length=USERNAME_MAX_LENGTH,
        validators=(unique_username_validator(),),
    )
    first_name = serializers.CharField(
        required=True,
        max_length=FIRST_NAME_MAX_LENGTH
    )
    last_name = serializers.CharField(
        required=True,
        max_length=LAST_NAME_MAX_LENGTH
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )

    class Meta:
        model = Account
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        read_only_fields = ('avatar', 'is_subscribed',)

    def create(self, validated_data):
        """Создание пользователя с хэшированием пароля."""
        user = Account.objects.create(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    """Основной сериализатор для чтения данных о пользователе."""

    avatar = serializers.ImageField(read_only=True)
    is_subscribed = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Account
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления/удаления аватара."""

    avatar = Base64ImageField(required=True)

    class Meta:
        model = Account
        fields = ('avatar',)


class SetPasswordSerializer(serializers.Serializer):
    """Сериализер для смены пароля."""

    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(ERROR_CURRENT_PASSWORD)
        return value

    def validate_new_password(self, value):
        user = self.context['request'].user
        validate_password(value, user)
        return value

    def create(self, validated_data):
        """Жертва архитектуре DRF - метод обязателен для абстрактного класса"""
        pass

    def update(self, instance, validated_data):
        """Жертва архитектуре DRF - метод обязателен для абстрактного класса"""
        pass


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Укороченный рецепт в подписках"""

    class Meta:
        model = Recipes
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionUserSerializer(serializers.ModelSerializer):
    """Сериализатор автора в подписках."""

    recipes = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    is_subscribed = serializers.BooleanField(read_only=True, default=False)
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

    class Meta:
        model = Account
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )
        read_only_fields = ('is_subscribed', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = None
        if request is not None:
            limit_str = request.query_params.get('recipes_limit')
            if limit_str is not None:
                try:
                    if str(limit_str).isdigit():
                        limit = int(limit_str)
                except (ValueError, TypeError):
                    limit = None
        if limit is None:
            limit = self.context.get('recipes_limit')
        qs = obj.recipes.all()
        if limit is not None:
            try:
                limit = int(limit)
                qs = qs[:limit]
            except (ValueError, TypeError):
                pass
        return ShortRecipeSerializer(qs, many=True, context=self.context).data

    def get_avatar(self, obj):
        return obj.avatar.url if obj.avatar else None


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализер для ингредиентов."""

    class Meta:
        model = Ingredients
        fields = ('id', 'name', 'measurement_unit')


class IngredientAmountSerializer(serializers.ModelSerializer):
    """Отображение ингредиентов в рецепте (чтение)."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.DecimalField(
        max_digits=MAX_DIGITS_AMOUNT,
        decimal_places=MAX_PLACES_AMOUNT,
        coerce_to_string=False,
        read_only=True
    )

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class AddIngredientSerializer(serializers.ModelSerializer):
    """Используется при создании/редактировании рецепта."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredients.objects.all(),
        source='ingredient'
    )

    class Meta:
        model = IngredientAmount
        fields = ('id', 'amount')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тэгов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class RecipeSerializer(serializers.ModelSerializer):
    """Полный сериализатор рецепта."""

    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientAmountSerializer(
        source='ingredient_amounts',
        many=True,
        read_only=True)
    image = Base64ImageField(read_only=True)
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


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Создание и редактирование рецепта."""

    image = Base64ImageField()
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    ingredients = AddIngredientSerializer(many=True, required=True)
    author = UserSerializer(read_only=True)

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
            'ingredients'
        )

    def validate(self, data):
        tags = data.get('tags')
        ingredients = data.get('ingredients') or []
        if not tags:
            raise serializers.ValidationError(
                {'tags': ERROR_NO_TAGS}
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': ERROR_TAGS_ARE_REPEATED}
            )
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients': ERROR_NO_INGREDIENT}
            )
        seen = set()
        for item in ingredients:
            ingredient = item['ingredient']
            if ingredient in seen:
                raise serializers.ValidationError(
                    {'ingredients': ERROR_INGREDIENT_ARE_REPEATED}
                )
            seen.add(ingredient)
            if float(item['amount']) <= 0:
                raise serializers.ValidationError(
                    {'ingredients': ERROR_ZERO_INGREDIEN_AMOUNT}
                )
        return data

    def create_ingredients(self, recipe, ingredients):
        objs = [
            IngredientAmount(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            ) for item in ingredients
        ]
        IngredientAmount.objects.bulk_create(objs)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipes.objects.create(
            **validated_data
        )
        recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if tags is not None:
            instance.tags.set(tags)
        if ingredients is not None:
            instance.ingredient_amounts.all().delete()
            self.create_ingredients(instance, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data
