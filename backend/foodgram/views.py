from django.http import Http404
from django.shortcuts import redirect

from .models import Recipes


def redirect_to_recipe(request, recipe_id):
    """
    Перенаправляет короткую ссылку на страницу рецепта по ID.
    """
    if not Recipes.objects.filter(pk=recipe_id).exists():
        raise Http404(f'Рецепта с id {recipe_id} не существует.')
    return redirect(f'/recipes/{recipe_id}/')
