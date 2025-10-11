from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (IngredientViewSet,
                    RecipeViewSet, TagViewSet, UserViewSet)

router = SimpleRouter()
router.register('users', UserViewSet, basename='users')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls), name='routers'),
]
