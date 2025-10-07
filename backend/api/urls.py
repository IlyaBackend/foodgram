from django.urls import include, path
from rest_framework.routers import SimpleRouter

from backend.constants import INGREDIENTS_URL, RESIPES_URL, TAGS_URL, USERS_URL

from .views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

router = SimpleRouter()
router.register(USERS_URL, UserViewSet, basename='users')
router.register(RESIPES_URL, RecipeViewSet, basename='recipes')
router.register(TAGS_URL, TagViewSet, basename='tags')
router.register(INGREDIENTS_URL, IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls), name='routers'),
]
