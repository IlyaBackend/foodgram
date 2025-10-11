import shortuuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models

from .constants import (EMAIL_MAX_LENGTH, MAX_LENGTH_INGREDIENT_NAME,
                        MAX_LENGTH_MEASUREMENT_UNIT, MAX_LENGTH_RECIPES_NAME,
                        MAX_LENGTH_TAG, MAX_LENGTH_TAG_SLUG, MIN_AMOUNT,
                        MIN_COOKING_TIME, STR_LENGTH, USERNAME_MAX_LENGTH)
from .validators import USERNAME_REGEX_VALIDATOR


class Account(AbstractUser):
    """Кастомная модель пользователя."""

    username = models.CharField(
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=(USERNAME_REGEX_VALIDATOR,),
        verbose_name='Юзернейм пользователя'
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
    """Модель для записи ингредиентов."""

    name = models.CharField(
        max_length=MAX_LENGTH_INGREDIENT_NAME,
        unique=True,
        verbose_name='Название ингридиента'
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
        max_length=MAX_LENGTH_TAG,
        unique=True,
        verbose_name='Тэг'
    )
    slug = models.SlugField(
        max_length=MAX_LENGTH_TAG_SLUG,
        unique=True,
        blank=False,
        verbose_name='Слаг'
    )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'
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
            MIN_COOKING_TIME, 'Время приготовления не меньше 1 минуты'
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
        verbose_name='Автор'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тэг',
        related_name='tags'
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        through='IngredientAmount',
        related_name='recipes'
    )
    short_code = models.CharField(
        max_length=22,
        unique=True,
        editable=False,
        verbose_name='Короткий код ссылки'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-created_at',)
        default_related_name = 'recipes'

    def __str__(self):
        return self.name[:STR_LENGTH]

    def save(self, *args, **kwargs):
        if not self.pk or not self.short_code:
            self.short_code = shortuuid.uuid()
        super().save(*args, **kwargs)


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
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        blank=False,
        verbose_name='Количество',
        validators=[MinValueValidator(
            MIN_AMOUNT, 'Количество должно быть больше нуля'
        )],
    )

    class Meta:
        verbose_name = 'Количество продукта в рецепте'
        verbose_name_plural = 'Количество продуктов в рецептах'
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


class FavoriteShoppingCartBase(models.Model):
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
        ordering = ('-id',)


class Favorite(FavoriteShoppingCartBase):
    """Избранные рецепты пользователей."""

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]
        default_related_name = 'favorites'

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class ShoppingCart(FavoriteShoppingCartBase):
    """Список покупок пользователей."""

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]
