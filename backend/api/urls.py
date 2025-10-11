from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import (IngredientViewSet, RecipeShortLinkRedirectView,
                    RecipeViewSet, TagViewSet, UserViewSet)

router = SimpleRouter()
router.register('users', UserViewSet, basename='users')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path(
        's/<str:short_code>/',
        RecipeShortLinkRedirectView.as_view(),
        name='recipe-short-link'),
    path('', include(router.urls), name='routers'),
]
