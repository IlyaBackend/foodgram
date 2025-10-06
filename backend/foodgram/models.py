from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from backend.constants import (MAX_DIGITS_AMOUNT, MAX_LENGTH_INGREDIENT_NAME,
                               MAX_LENGTH_MEASUREMENT_UNIT,
                               MAX_LENGTH_RECIPES_NAME, MAX_LENGTH_TAG,
                               MAX_LENGTH_TAG_SLUG, MAX_PLACES_AMOUNT,
                               STR_LENGTH)


class Ingredients(models.Model):
    """Модель для записи ингредиентов."""

    name = models.CharField(
        max_length=MAX_LENGTH_INGREDIENT_NAME,
        unique=True,
        blank=False,
        verbose_name='Название ингридиента'
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_MEASUREMENT_UNIT,
        blank=False,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']

    def __str__(self):
        return f'{self.name[:STR_LENGTH]}'


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_LENGTH_TAG,
        unique=True,
        blank=False,
        verbose_name='Тэг'
    )
    slug = models.SlugField(
        max_length=MAX_LENGTH_TAG_SLUG,
        unique=True,
        blank=False,
        verbose_name='ТэгСлаг'
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return f'{self.name[:STR_LENGTH]}'


class Recipes(models.Model):
    """Модель для рецептов."""

    name = models.CharField(
        max_length=MAX_LENGTH_RECIPES_NAME,
        blank=False,
        verbose_name='Название рецепта'
    )
    text = models.TextField(
        blank=False,
        verbose_name='Описание'
    )
    cooking_time = models.PositiveIntegerField(
        blank=False,
        validators=[MinValueValidator(
            1, 'Время приготовления не меньше 1 минуты'
        )],
        verbose_name='Время приготовления в минутах'
    )
    image = models.ImageField(
        upload_to='foodgram',
        blank=False,
        verbose_name='Фотография блюда'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=False,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэг'
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        through='IngredientAmount',
        related_name='recipe_ingredients'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.name[:STR_LENGTH]}'


class IngredientAmount(models.Model):
    """
    Через эту модель будут связаны Recipes <-> Ingredients указывает
    количества продукта в рецепте.
    """

    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='ingredient_amounts',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        related_name='recipe_amounts',
        verbose_name='Ингредиент'
    )
    amount = models.DecimalField(
        max_digits=MAX_DIGITS_AMOUNT,
        decimal_places=MAX_PLACES_AMOUNT,
        verbose_name='Количество',
        validators=[MinValueValidator(
            0.01, 'Количество должно быть больше нуля'
        )],
    )

    class Meta:
        verbose_name = 'Количество ингредиента в рецепте'
        verbose_name_plural = 'Количество ингредиентов в рецептах'
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


class Favorite(models.Model):
    """Избранные рецепты пользователей."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Рецепт'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        ordering = ('-created_at',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class ShoppingCart(models.Model):
    """Список покупок пользователей."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='пользователь'
    )
    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='in_carts',
        verbose_name='Рецепт'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        ordering = ('-created_at',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]
