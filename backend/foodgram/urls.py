from django.urls import path

from .views import redirect_to_recipe

urlpatterns = [
    path(
        's/<int:recipe_id>/',
        redirect_to_recipe,
        name='recipe-short-link'
    ),
]
