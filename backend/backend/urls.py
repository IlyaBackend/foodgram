from django.contrib import admin
from django.urls import include, path
from api.views import RecipeShortLinkRedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path(
        's/<str:short_code>/',
        RecipeShortLinkRedirectView.as_view(),
        name='recipe-short-link'),
]
