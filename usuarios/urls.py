from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from . import views
from .views import (
    aprobar_blog, blog_detalle, gestionar_blog, adicionar_blog, aprobar_testimonio
)
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    # Restablecimiento de contraseña
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='usuarios/password_reset.html'), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='usuarios/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='usuarios/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='usuarios/password_reset_complete.html'), name='password_reset_complete'),

    # Usuarios
    path('usuario/', views.usuario_view, name='usuario'),
    path('profile/', views.profile, name='profile'),
    path('mensajes_recibidos/', views.mensajes_recibidos, name='mensajes_recibidos'),
    path('ver_citas/', views.ver_citas, name='ver_citas'),
    path('reservar_cita/', views.reservar_cita, name='reservar_cita'),
    path('agregar_testimonio/', views.agregar_testimonio, name='agregar_testimonio'),
    path('testimonios/', views.testimonios, name='testimonios'),

    # Especialistas
    path('especialista/', views.especialista_view, name='especialista'),
    path('get_especialistas/<int:especialidad_id>/', views.get_especialistas, name='get_especialistas'),

    # Administración
    path('administrador/', include([
        path('', views.admin_view, name='administrador'),
        path('panel/', views.panel_administrador, name='panel_administrador'),
        path('usuarios/', views.gestionar_usuarios, name='gestionar_usuarios'),
        path('especialistas/', views.gestionar_especialistas, name='gestionar_especialistas'),
        path('add_especialista/', views.add_especialista, name='add_especialista'),
        path('add_admin/', views.add_admin, name='add_admin'),
        path('editar_usuario/<int:usuario_id>/', views.editar_usuario, name='editar_usuario'),
        path('eliminar_usuario/<int:usuario_id>/', views.eliminar_usuario, name='eliminar_usuario'),
        path('editar_especialista/<int:especialista_id>/', views.editar_especialista, name='editar_especialista'),  # Eliminada la redundancia "administrador/"
        path('eliminar_especialista/<int:especialista_id>/', views.eliminar_especialista, name='eliminar_especialista'),  # Eliminada la redundancia "administrador/"
        path('gestionar_disponibilidad/', views.gestionar_disponibilidad, name='gestionar_disponibilidad'),
        path('añadir_disponibilidad/', views.añadir_disponibilidad, name='añadir_disponibilidad'),
        path('obtener_disponibilidad/<int:especialista_id>/', views.obtener_disponibilidad, name='obtener_disponibilidad'),
        path('registrar_cita/', views.registrar_cita, name='registrar_cita'),
        path('citas/', views.gestionar_citas_admin, name='gestionar_citas_admin'),
        path('citas/editar/<int:cita_id>/', views.editar_cita, name='editar_cita'),
        path('citas/cancelar/<int:cita_id>/', views.cancelar_cita, name='cancelar_cita'),
        path('citas/aprobar/<int:cita_id>/', views.aprobar_cita, name='aprobar_cita'),
        path('delete_cita/<int:cita_id>/', views.delete_cita, name='delete_cita'),
        path('testimonios/', views.gestionar_testimonios, name='gestionar_testimonios'),
        path('testimonios/ocultar/<int:testimonio_id>/', views.ocultar_testimonio, name='ocultar_testimonio'),
        path('aprobar_testimonio/<int:testimonio_id>/', aprobar_testimonio, name='aprobar_testimonio'),
        path('blogs/', gestionar_blog, name='gestionar_blog'),
        path('adicionar_blog/', adicionar_blog, name='adicionar_blog'),
        path('aprobar_blog/<int:blog_id>/', aprobar_blog, name='aprobar_blog'),
        path('administrador/editar_disponibilidad/<int:disponibilidad_id>/', views.editar_disponibilidad, name='editar_disponibilidad'),


    ])),

    # Blogs
    path('blog/<int:blog_id>/', blog_detalle, name='blog_detalle'),
]

# Archivos estáticos en modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)