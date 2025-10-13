from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', include('foodgram.urls')),
    path(
        'api/docs/',
        TemplateView.as_view(template_name='docs/redoc.html'),
        name='redoc'
    ),
]
