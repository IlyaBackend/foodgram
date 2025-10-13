# isort: skip_file
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models

from .constants import (
    EMAIL_MAX_LENGTH, FIRST_NAME_MAX_LENGTH,
    LAST_NAME_MAX_LENGTH, MAX_LENGTH_INGREDIENT_NAME,
    MAX_LENGTH_MEASUREMENT_UNIT, MAX_LENGTH_RECIPES_NAME,
    MAX_LENGTH_TAG_NAME, MAX_LENGTH_TAG_SLUG, MIN_AMOUNT,
    MIN_COOKING_TIME, STR_LENGTH, USERNAME_MAX_LENGTH
)
from .validators import USERNAME_REGEX_VALIDATOR


class Account(AbstractUser):
    """Кастомная модель пользователя."""

    first_name = models.CharField(
        max_length=FIRST_NAME_MAX_LENGTH,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=LAST_NAME_MAX_LENGTH,
        verbose_name='Фамилия'
    )
    username = models.CharField(
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=(USERNAME_REGEX_VALIDATOR,),
        verbose_name='Юзернейм'
    )
    email = models.EmailField(
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
        verbose_name='Эл.почта'
    )
    avatar = models.ImageField(
        upload_to='users',
        null=True,
        blank=True,
        default=None,
        verbose_name='Аватар'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписок, на кого я подписан и кто подписна на меня."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='authors',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'


class Ingredients(models.Model):
    """Модель для записи продуктов."""

    name = models.CharField(
        max_length=MAX_LENGTH_INGREDIENT_NAME,
        unique=True,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_MEASUREMENT_UNIT,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'продукт'
        verbose_name_plural = 'продукты'
        ordering = ('name',)

    def __str__(self):
        return self.name[:STR_LENGTH]


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH_TAG_NAME,
        unique=True,
        verbose_name='Метка'
    )
    slug = models.SlugField(
        max_length=MAX_LENGTH_TAG_SLUG,
        unique=True,
        blank=False,
        verbose_name='Слаг'
    )

    class Meta:
        verbose_name = 'Метка'
        verbose_name_plural = 'Метки'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name[:STR_LENGTH]}'


class Recipes(models.Model):
    """Модель для рецептов."""

    name = models.CharField(
        max_length=MAX_LENGTH_RECIPES_NAME,
        verbose_name='Название'
    )
    text = models.TextField(
        blank=False,
        verbose_name='Описание'
    )
    cooking_time = models.PositiveIntegerField(
        blank=False,
        validators=[MinValueValidator(
            MIN_COOKING_TIME,
            f'Время приготовления не меньше {MIN_COOKING_TIME} минуты'
        )],
        verbose_name='Время (мин)'
    )
    image = models.ImageField(
        upload_to='foodgram',
        blank=False,
        null=False,
        verbose_name='Изображение'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=False,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Метка',
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        through='IngredientAmount',
        related_name='recipes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)
        default_related_name = 'recipes'

    def __str__(self):
        return self.name[:STR_LENGTH]


class IngredientAmount(models.Model):
    """
    Через эту модель будут связаны Recipes <-> Ingredients указывает
    количества продукта в рецепте.
    """

    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        related_name='ingredient_amounts',
        verbose_name='продукт'
    )
    amount = models.PositiveIntegerField(
        blank=False,
        verbose_name='Количество',
        validators=[MinValueValidator(
            MIN_AMOUNT, f'Минимум {MIN_AMOUNT}'
        )],
    )

    class Meta:
        verbose_name = 'Продукт рецепта'
        verbose_name_plural = 'Продукты рецепта'
        default_related_name = 'ingredient_amounts'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient_amount'
            )
        ]

    def __str__(self):
        return (
            f'{self.ingredient.name} — {self.amount} '
            f'{self.ingredient.measurement_unit}.'
        )


class UserRecipeRelation(models.Model):
    """Базовая модель для избранного и корзиной покупок"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_%(app_label)s_%(class)s_relation'
            )
        ]
        default_related_name = '%(class)ss'

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class Favorite(UserRecipeRelation):
    """Избранные рецепты пользователей."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(UserRecipeRelation):
    """Список покупок пользователей."""

    class Meta(UserRecipeRelation.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
