# пользователь
USERNAME_MAX_LENGTH = 64
EMAIL_MAX_LENGTH = 254
FIRST_NAME_MAX_LENGTH = 150
LAST_NAME_MAX_LENGTH = 150
REGULAR_USERNAME = r'^[\w.@+-]+\Z'
MY_USER_PROFILE = 'me'

# рецепты
MAX_LENGTH_INGREDIENT_NAME = 256
MAX_LENGTH_MEASUREMENT_UNIT = 20
MAX_LENGTH_TAG = 30
MAX_LENGTH_TAG_SLUG = 64
MAX_LENGTH_RECIPES_NAME = 256
STR_LENGTH = 31
MAX_DIGITS_AMOUNT = 9
MAX_PLACES_AMOUNT = 3

# ошибки
ERROR_USERNAME_SYMBOLS = (
    'Имя пользователя может содержать'
    'буквы, цифры, и некоторые знаки'
)
ERROR_USERNAME_IS_BUISY = 'Пользователь с таким юзернеймом уже существует'
ERROR_MESSAGE_EMAIL_IS_BUSY = 'Пользователь с таким email уже существует'
ERROR_ZERO_INGREDIEN_AMOUNT = 'Количество должно быть больше нуля.'
ERROR_INGREDIENT_ARE_REPEATED = 'Ингредиенты не должны повторяться.'
ERROR_NO_INGREDIENT = 'Нужно добавить хотя бы один ингредиент.'
ERROR_TAGS_ARE_REPEATED = 'Теги не должны повторяться.'
ERROR_NO_TAGS = 'Нужно указать хотя бы один тег.'
ERROR_CURRENT_PASSWORD = 'Неверный текущий пароль.'
ERROR_AVATAR_PUT = 'Это поле обязательно.'
ERROR_SUBSCRIE_TO_YOURSELF = 'Нельзя подписаться на самого себя.'
ERROR_ALREADY_SIGNED = 'Вы уже подписаны на этого пользователя.'
ERROR_YOU_ARE_NOT_SUBSCRIBED = 'Вы не подписаны на этого пользователя.'
ERROR_RECIPE_IN_FAVORITES = 'Рецепт уже в избранном.'
ERROR_RECIPE_NOT_IN_FAVORITES = 'Рецепта нет в избранном.'
ERROR_RECIPE_IN_SHOPPING_CART = 'Рецепт уже в списке покупок.'
ERROR_RECIPE_NOT_IN_SHOPPING_CART = 'Рецепта нет в списке покупок.'

# Название файла со списком покупок
FILE_NAME_SHOPPING_CART = "Надо купить.txt"

# Пагинация
PAGE_SIZE_QUERY_PARAM = 'limit'
PAGE_SIZE = 6
MAX_PAGE_SIZE = 100

# urls
RESIPES_URL = 'recipes'
TAGS_URL = 'tags'
INGREDIENTS_URL = 'ingredients'
USERS_URL = 'users'
