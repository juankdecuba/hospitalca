from django.contrib import admin
from usuarios import views
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('usuarios.urls')),  # Incluye las URLs de la app `usuarios`
    path('', views.login_view, name='login'),
]