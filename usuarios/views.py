from datetime import datetime
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.cache import cache_page 
from django.contrib.auth.views import PasswordResetView
from pytest import Session
from .models import Disponibilidad
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
import re
from django.core.cache import cache 
from django.utils.timezone import now
from django.contrib.messages import get_messages
from .forms import TestimonioForm,CitaForm,BlogForm,EspecialistaCreationForm,DisponibilidadForm
from .models import Cita, Especialista, Usuario, Especialidad, Profile,Testimonio,Blog,Mensaje
from django.contrib.admin.views.decorators import staff_member_required
import json
from django.contrib.auth.models import User
User = get_user_model()

# views.py (versión definitiva)
logger = logging.getLogger(__name__)


def is_admin(user):
    return user.is_authenticated and (user.is_superuser or getattr(user, 'es_admin', False))

def is_especialista(user):
    return user.is_authenticated and getattr(user, 'es_especialista', False)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not password:
            messages.error(request, '⚠️ Usuario y contraseña requeridos.')
            return render(request, 'usuarios/login.html', {'username': username, 'next': request.POST.get('next', '')})

        # Verificar intentos fallidos
        failed_attempts = cache.get(f"failed_login_{username}", 0)
        if failed_attempts >= 5:
            messages.error(request, "🚫 Demasiados intentos fallidos. Intenta nuevamente en unos minutos.")
            return render(request, 'usuarios/login.html', {'username': username, 'next': request.POST.get('next', '')})

        # Autenticar usuario
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                cache.delete(f"failed_login_{username}")  # 🔹 Resetear intentos fallidos

                # Limpia los mensajes residuales
                storage = get_messages(request)
                for _ in storage:
                    pass

                next_url = request.POST.get('next', '')
                if next_url:
                    return redirect(next_url)
                elif user.is_superuser or getattr(user, 'es_admin', False):
                    return redirect(reverse('administrador'))
                elif getattr(user, 'es_especialista', False):
                    return redirect(reverse('especialista'))
                else:
                    return redirect(reverse('usuario'))
            else:
                messages.error(request, '🚫 Cuenta desactivada.')
        else:
            cache.set(f"failed_login_{username}", failed_attempts + 1, timeout=300)  # 🔹 Bloqueo por 5 min tras 5 intentos
            messages.error(request, '⚠️ Usuario o contraseña incorrectos.')

        return render(request, 'usuarios/login.html', {'username': username, 'next': request.POST.get('next', '')})

    return render(request, 'usuarios/login.html', {'next': request.GET.get('next', '')})

def register_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')

        # Validar contraseña segura
        pattern = r'^(?=.*[A-Z])(?=.*\d)(?=.*[@#$%*^&+=!])\S{8,}$'
        if not re.match(pattern, password):
            error = "⚠️ La contraseña debe tener al menos 8 caracteres y símbolos especiales."

        elif User.objects.filter(username=username).exists():
            error = "⚠️ El nombre de usuario ya está en uso."
        
        else:
            # Crear usuario con contraseña segura
            user = Usuario.objects.create(
                username=username,
                password=make_password(password),  # 🔹 Aplica hashing seguro
                email=email,
                is_active=True  # 🔹 Activa la cuenta
            )
            login(request, user)
            return redirect('usuario')  # Redirige al panel de usuario
    
    return render(request, 'usuarios/register.html', {'error': error})



# def clear_all_sessions():
#     Session.objects.all().delete()
# clear_all_sessions()
    

@login_required
@staff_member_required
def add_especialista(request):
    """Creación de especialistas accesible solo para administradores."""
    if request.method == 'POST':
        form = EspecialistaCreationForm(request.POST)
        if form.is_valid():
            form.save()  # El formulario ya maneja la creación del usuario y el especialista
            messages.success(request, "✅ Especialista creado exitosamente.")
            return redirect('gestionar_especialistas')  # Redirige a la lista de especialistas
        else:
            messages.error(request, "⚠️ Error al crear el especialista. Verifica los datos ingresados.")
    else:
        form = EspecialistaCreationForm()

    return render(request, 'administrador/add_especialista.html', {'form': form})



@login_required
@user_passes_test(is_admin)
def register_admin_view(request):
    error = None
    role = request.GET.get('role', 'especialista')  # Obtener el rol desde la URL

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']

        if User.objects.filter(username=username).exists():
            error = "El nombre de usuario ya está en uso."
        else:
            user = User.objects.create_user(username=username, password=password, email=email)
            if role == 'especialista':
                user.es_especialista = True
            elif role == 'administrador':
                user.es_admin = True
            user.save()
            return redirect('administrador')  # Redirigir al panel de administrador

    return render(request, 'usuarios/register_admin.html', {'error': error, 'role': role})


@login_required
@user_passes_test(is_admin, login_url='/login/')
def admin_view(request):
    from .models import Usuario  # Importar aquí para evitar circular imports
    total_usuarios = Usuario.objects.count()
    
    context = {
        'total_usuarios': total_usuarios,
        # ... otras estadísticas ...
    }
    return render(request, 'usuarios/administrador.html', context)


@login_required
@user_passes_test(is_admin)
def add_admin(request):
    error = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']

        if User.objects.filter(username=username).exists():
            error = "El nombre de usuario ya está en uso."
        else:
            user = User.objects.create_user(username=username, password=password, email=email)
            user.es_admin = True
            user.save()
            return redirect('administrador')
    return render(request, 'usuarios/add_admin.html', {'error': error})

@login_required
@staff_member_required
def edit_cita(request, cita_id):
    """Edición de citas accesible solo para administradores."""
    cita = get_object_or_404(Cita, id=cita_id)

    if request.method == 'POST':
        cita.usuario = get_object_or_404(Usuario, id=request.POST['usuario'])
        cita.especialista = get_object_or_404(Usuario, id=request.POST['especialista'])
        cita.fecha_hora = request.POST['fecha_hora']
        cita.save()
        messages.success(request, "✅ Cita editada correctamente.")
        return redirect('administrador')

    return render(request, 'usuarios/edit_cita.html', {'cita': cita})

@login_required
@staff_member_required
def delete_cita(request, cita_id):
    """Elimina citas con seguridad para evitar eliminaciones accidentales."""
    cita = get_object_or_404(Cita, id=cita_id)

    if request.method == 'POST':
        cita.delete()
        messages.success(request, "❌ Cita eliminada correctamente.")
        return redirect('administrador')

    return render(request, 'usuarios/delete_cita.html', {'cita': cita})


@login_required(login_url='login')
def testimonials(request):
    return render(request, 'usuarios/testimonials.html') 



@login_required
@user_passes_test(is_especialista, login_url='/login/')
def especialista_view(request):
    print(f"[DEBUG] Usuario intentando acceder: {request.user.username}")
    print(f"[DEBUG] es_especialista: {request.user.es_especialista}")
    
    especialista = request.user
    
    if not especialista.es_especialista:
        print("[DEBUG] El usuario no es especialista, redirigiendo...")
        return redirect('usuario')
    
    citas = Cita.objects.filter(especialista=especialista).select_related('usuario', 'especialidad')
    print(f"[DEBUG] Número de citas encontradas: {citas.count()}")

    return render(request, 'usuarios/especialista.html', {
        'especialista': especialista,
        'citas': citas,
    })


@login_required
def reservar_cita(request):
    """Permite a los usuarios reservar citas con validaciones de disponibilidad."""
    # Limpia mensajes residuales
    storage = get_messages(request)
    for _ in storage:
        pass

    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            fecha_hora = form.cleaned_data['fecha_hora']
            especialista = form.cleaned_data['especialista']

            if fecha_hora < now():
                messages.error(request, "⚠️ No puedes reservar una cita para días pasados.")
            elif Cita.objects.filter(especialista=especialista, fecha_hora=fecha_hora).exists():
                messages.error(request, "⚠️ El especialista ya tiene una cita programada para esta fecha.")
            else:
                cita = form.save(commit=False)
                cita.usuario = request.user
                cita.estado = 'pendiente'
                cita.save()

                messages.success(request, "✅ Cita reservada correctamente.")
                return render(request, 'usuarios/reservar_cita.html', {
                    'form': CitaForm(),  # Reinicia el formulario
                    'especialidades': Especialidad.objects.all(),
                    'especialistas': Usuario.objects.filter(es_especialista=True).values('id', 'username', 'especialidad_id'),
                    'ahora': now().strftime('%Y-%m-%dT%H:%M'),
                })

        else:
            messages.error(request, "⚠️ Error al reservar la cita. Verifica los datos.")
    else:
        form = CitaForm()

    ahora = now().strftime('%Y-%m-%dT%H:%M')
    especialidades = Especialidad.objects.all()
    especialistas = Usuario.objects.filter(es_especialista=True).values('id', 'username', 'especialidad_id')

    return render(request, 'usuarios/reservar_cita.html', {
        'form': form,
        'especialidades': especialidades,
        'especialistas': especialistas,
        'ahora': ahora,
    })


@login_required
def ver_citas(request):
    citas = Cita.objects.filter(usuario=request.user)
    return render(request, 'usuarios/ver_citas.html', {'citas': citas})   

@login_required
def usuario_view(request):
    """Vista principal para usuarios normales."""
    # Redirección según el tipo de usuario
    if getattr(request.user, 'es_admin', False) or request.user.is_superuser:
        return redirect('administrador')
    if getattr(request.user, 'es_especialista', False):
        return redirect('especialista')
    
    # Obtener citas del usuario
    citas = Cita.objects.filter(usuario=request.user).select_related('especialista', 'especialidad').order_by('fecha_hora')

    # Obtener testimonios aprobados
    try:
        testimonios = Testimonio.objects.filter(aprobado=True).select_related('usuario').values(
            'usuario__username', 'experiencia', 'comentario', 'fecha_publicacion'
        )
    except Exception as e:
        testimonios = []
        messages.error(request, f"⚠️ Error al cargar testimonios: {str(e)}")

    # Contar mensajes no leídos
    mensajes_no_leidos = Mensaje.objects.filter(destinatario=request.user, leido=False).count()

    # Blogs aprobados (si es necesario mostrar blogs en la página)
    blogs = Blog.objects.filter(aprobado=True).order_by('-fecha_publicacion')[:5]  # Limitar a los 5 más recientes

    return render(request, 'usuarios/usuario.html', {
        'user': request.user,
        'citas': citas,
        'testimonios': testimonios,
        'mensajes_no_leidos': mensajes_no_leidos,
        'blogs': blogs,  # Incluye blogs si es necesario
    })

@login_required
def ocultar_testimonio(request, testimonio_id):
    """Oculta un testimonio marcándolo como no aprobado."""
    testimonio = get_object_or_404(Testimonio, id=testimonio_id)
    testimonio.aprobado = False
    testimonio.save()
    messages.success(request, f"El testimonio de {testimonio.usuario.username} ha sido ocultado.")
    return redirect('gestionar_testimonios')  # Cambia 'gestionar_testimonios' por el nombre de tu vista


def get_especialistas(request, especialidad_id):
    """Devuelve los especialistas filtrados por especialidad en formato JSON."""
    especialistas = Usuario.objects.filter(especialidad_id=especialidad_id, es_especialista=True)
    data = [{'id': e.id, 'username': e.username} for e in especialistas]
    return JsonResponse(data, safe=False)

# @cache_page(60 * 15)
@login_required
def profile(request):
    """Muestra las citas del usuario en categorías organizadas."""
    profile, created = Profile.objects.get_or_create(user=request.user)

    # Optimización: Usar select_related para reducir consultas
    citas_pendientes = Cita.objects.filter(usuario=request.user, estado='pendiente')
    citas_aceptadas = Cita.objects.filter(usuario=request.user, estado='aceptada')
    citas_rechazadas = Cita.objects.filter(usuario=request.user, estado='rechazada')

    return render(request, 'usuarios/profile.html', {
        'profile': profile,
        'citas_pendientes': citas_pendientes,
        'citas_aceptadas': citas_aceptadas,
        'citas_rechazadas': citas_rechazadas,
    })


@login_required
def editar_cita(request, cita_id):
    """Permite a los usuarios reprogramar citas rechazadas y cambiarlas a 'pendiente'."""
    cita = get_object_or_404(Cita, id=cita_id)

    if request.method == 'POST':
        form = CitaForm(request.POST, instance=cita)
        if form.is_valid():
            cita.estado = "pendiente"  # 🔹 Cambia el estado de la cita a pendiente para revisión
            form.save()
            messages.success(request, "✅ Cita reprogramada correctamente y enviada para aprobación.")
            return redirect('profile')  # Redirige al perfil del usuario
        else:
            messages.error(request, "⚠️ Error al actualizar la cita.")
    else:
        form = CitaForm(instance=cita)

    especialidades = Especialidad.objects.all()
    especialistas = Usuario.objects.filter(es_especialista=True, especialidad_id=cita.especialidad.id)

    return render(request, 'usuarios/editar_cita.html', {
        'form': form,
        'cita': cita,
        'especialidades': especialidades,
        'especialistas': especialistas,  # Eliminado JSON para mejor manejo directo
    })


@login_required
def cancelar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id, usuario=request.user)  # Validar que la cita pertenece al usuario
    if request.method == 'POST':
        cita.delete()  # Elimina la cita de la base de datos
        return redirect('profile')  # Redirige al perfil o a otra página
    return render(request, 'usuarios/cancelar_cita.html', {'cita': cita})


    
    
def logout_view(request):
    if request.method == 'POST' or request.method == 'GET':
        logout(request)
        return redirect('login')

@login_required
@staff_member_required
def panel_administrador(request):
    """Panel solo accesible por administradores."""
    try:
        # Obtener datos detallados
        usuarios = Usuario.objects.values('username', 'email', 'date_joined')
        especialistas = Usuario.objects.filter(es_especialista=True).select_related('especialidad').values('username', 'especialidad__nombre')
        citas = Cita.objects.select_related('especialista', 'usuario').values('usuario__username', 'especialista__username', 'fecha_hora', 'descripcion')
        testimonios = Testimonio.objects.filter(aprobado=True).select_related('usuario').values('usuario__username', 'experiencia', 'comentario', 'fecha_publicacion')

        # Calcular estadísticas
        usuarios_count = Usuario.objects.count()
        especialistas_count = Usuario.objects.filter(es_especialista=True).count()
        citas_count = Cita.objects.count()
        blogs_count = Blog.objects.count()

        # Debugging: Imprimir valores en la consola
        print(f"Usuarios: {usuarios_count}, Especialistas: {especialistas_count}, Citas: {citas_count}, Blogs: {blogs_count}")

    except Exception as e:
        # Manejo de errores
        messages.error(request, f"⚠️ Error al cargar datos: {str(e)}")
        usuarios, especialistas, citas, testimonios = [], [], [], []
        usuarios_count, especialistas_count, citas_count, blogs_count = 0, 0, 0, 0

    return render(request, 'usuarios/administrador.html', {
        'usuarios': usuarios,
        'especialistas': especialistas,
        'citas': citas,
        'testimonios': testimonios,
        'usuarios_count': usuarios_count,
        'especialistas_count': especialistas_count,
        'citas_count': citas_count,
        'blogs_count': blogs_count,
    })


from django.core.paginator import Paginator  # Asegúrate de que Paginator esté importado

@staff_member_required
@login_required
@cache_page(60 * 15)  # Cachear la vista por 15 minutos
def gestionar_citas_admin(request):
    """Vista para gestionar citas desde el panel de administración"""
    # Optimización: Usar select_related para reducir consultas
    citas_pendientes = Cita.objects.filter(estado='pendiente').select_related('usuario', 'especialista')
    citas_aceptadas = Cita.objects.filter(estado='aceptada').select_related('usuario', 'especialista')
    citas_rechazadas = Cita.objects.filter(estado='rechazada').select_related('usuario', 'especialista')

    # Paginación para citas pendientes
    paginator = Paginator(citas_pendientes, 10)  # Mostrar 10 citas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)  # Define page_obj aquí

    if request.method == 'POST':
        cita_id = request.POST.get('cita_id')
        accion = request.POST.get('accion')
        cita = get_object_or_404(Cita, id=cita_id)

        if accion == 'aceptar':
            cita.estado = 'aceptada'
            cita.save()
            Mensaje.objects.create(
                remitente=request.user,
                destinatario=cita.usuario,
                contenido=f"Tu cita con el especialista {cita.especialista.username} para el {cita.fecha_hora} ha sido aceptada."
            )
            messages.success(request, f"✅ Cita con {cita.usuario.username} aceptada.")
        elif accion == 'rechazar':
            motivo = request.POST.get('motivo_rechazo', '').strip()
            if not motivo:
                messages.error(request, "⚠️ Debes escribir un motivo de rechazo.")
                return redirect('gestionar_citas_admin')

            cita.estado = 'rechazada'
            cita.motivo_rechazo = motivo
            cita.save()
            Mensaje.objects.create(
                remitente=request.user,
                destinatario=cita.usuario,
                contenido=f"Tu cita con el especialista {cita.especialista.username} para el {cita.fecha_hora} ha sido rechazada. Motivo: {motivo}"
            )
            messages.warning(request, f"❌ Cita con {cita.usuario.username} rechazada. Motivo: {motivo}")

        return redirect('gestionar_citas_admin')

    return render(request, 'administrador/citas.html', {
        'page_obj': page_obj,  # Paginación para citas pendientes
        'citas_aceptadas': citas_aceptadas,
        'citas_rechazadas': citas_rechazadas,
    })


@login_required
def mis_citas(request):
    citas_aceptadas = Cita.objects.filter(usuario=request.user, estado='aceptada')
    return render(request, 'usuarios/profile.html', {'citas': citas_aceptadas})

@login_required
@staff_member_required
def gestionar_usuarios(request):
    usuarios = Usuario.objects.filter(es_especialista=False)  # Excluye especialistas
    return render(request, 'administrador/usuarios.html', {'usuarios': usuarios})


@login_required
@staff_member_required
def gestionar_especialistas(request):
    """Muestra la lista de especialistas disponibles."""
    especialistas = Usuario.objects.filter(es_especialista=True)
    return render(request, 'administrador/especialistas.html', {'especialistas': especialistas})

@login_required
def mensajes_recibidos(request):
    mensajes = Mensaje.objects.filter(destinatario=request.user).order_by('-fecha')
    # Marcar todos los mensajes como leídos
    mensajes.update(leido=True)
    return render(request, 'usuarios/mensajes_recibidos.html', {'mensajes': mensajes})
def mensajes_no_leidos(request):
    if request.user.is_authenticated:
        return Mensaje.objects.filter(destinatario=request.user, leido=False).count()
    return 0

@login_required
@staff_member_required
@cache_page(60 * 15)  # Cachear la vista por 15 minutos
def gestionar_blog(request):
    """Lista todos los blogs para que el administrador pueda gestionarlos."""
    # Optimización: Paginación para blogs
    blogs = Blog.objects.all().order_by('-fecha_publicacion')
    paginator = Paginator(blogs, 10)  # Mostrar 10 blogs por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'administrador/blogs.html', {'page_obj': page_obj})

def blog_detalle(request, blog_id):
    blog = get_object_or_404(Blog, id=blog_id)
    return render(request, 'usuarios/blog_detalle.html', {'blog': blog})

def adicionar_blog(request):
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES)  # Importante: request.FILES para imágenes
        if form.is_valid():
            form.save()
            return redirect('gestionar_blog')  # Redirigir a la lista de blogs después de guardar
    else:
        form = BlogForm()
    
    return render(request, 'administrador/add_blog.html', {'form': form})

def usuario_blogs(request):  # Renombramos la segunda vista
    blogs = Blog.objects.filter(aprobado=True) 
    return render(request, 'usuarios/usuario.html', {'blogs': blogs})

@login_required
@staff_member_required
def aprobar_blog(request, blog_id):
    """Cambia el estado del blog (aprobado/no aprobado) desde el panel."""
    blog = get_object_or_404(Blog, id=blog_id)
    blog.aprobado = not blog.aprobado  # Alternar el estado de aprobación
    blog.save()
    estado = "aprobado" if blog.aprobado else "desactivado"
    messages.success(request, f"✅ El blog '{blog.titulo}' ha sido {estado}.")
    return redirect('gestionar_blog')

@login_required
def agregar_testimonio(request):
    if request.method == 'POST':
        form = TestimonioForm(request.POST)
        if form.is_valid():
            testimonio = form.save(commit=False)
            testimonio.usuario = request.user
            testimonio.aprobado = False  # Los testimonios deben ser aprobados por el administrador
            testimonio.save()
            messages.success(request, "✅ ¡Gracias por tu testimonio! Será revisado antes de publicarse.")
            return redirect('usuario')  # Redirige al perfil del usuario
        else:
            messages.error(request, "⚠️ Hubo un error al enviar tu testimonio.")
    else:
        form = TestimonioForm()

    return render(request, 'usuarios/testimonials.html', {'form': form})


def testimonios(request):
    """Carga únicamente los testimonios aprobados en la página de usuarios."""
    testimonios = Testimonio.objects.filter(aprobado=True).order_by('-fecha_publicacion')  # 🔹 Ordenar por fecha
    return render(request, 'usuarios/usuario.html', {'testimonios': testimonios})


@login_required
@staff_member_required
def aprobar_testimonio(request, testimonio_id):
    """Cambia el estado de aprobación de un testimonio y envía respuesta JSON si es AJAX."""
    testimonio = get_object_or_404(Testimonio, id=testimonio_id)

    # Cambiar estado de aprobación
    testimonio.aprobado = not testimonio.aprobado  
    testimonio.save()

    # Verificar si la solicitud es AJAX para no recargar la página
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({"success": True, "aprobado": testimonio.aprobado})

    messages.success(request, "✅ Estado del testimonio cambiado.")
    return redirect('gestionar_testimonios')

@login_required
@staff_member_required
@cache_page(60 * 15)  # Cachear la vista por 15 minutos
def gestionar_testimonios(request):
    """Administra la gestión de testimonios en el panel."""
    # Optimización: Usar select_related para reducir consultas
    testimonios = Testimonio.objects.select_related('usuario').all()
    return render(request, 'administrador/testimonios.html', {'testimonios': testimonios})



@login_required
def aprobar_cita(request, cita_id):
    """Marca una cita como aceptada y muestra un mensaje de éxito."""
    cita = get_object_or_404(Cita, id=cita_id)
    
    if cita.estado == 'pendiente':  # Solo permitir aprobar citas pendientes
        cita.estado = 'aceptada'
        cita.save()
        messages.success(request, f"✅ Cita aprobada para {cita.usuario.username}.")
    else:
        messages.warning(request, "❗ Solo puedes aprobar citas pendientes.")
    
    return redirect('gestionar_citas')  # Redirigir al panel de gestión de citas


@login_required
def cancelar_cita(request, cita_id):
    """El usuario puede cancelar solo sus propias citas."""
    cita = get_object_or_404(Cita, id=cita_id, usuario=request.user)
    if request.method == 'POST':  
        cita.delete()
        messages.success(request, "❌ Cita cancelada correctamente.")
        return redirect('profile')  

    return render(request, 'usuarios/cancelar_cita.html', {'cita': cita})

@login_required
@staff_member_required
def editar_usuario(request, usuario_id):
    """Permite a los administradores editar usuarios."""
    usuario = get_object_or_404(Usuario, id=usuario_id)

    if request.method == 'POST':
        usuario.username = request.POST.get('username', usuario.username)
        usuario.email = request.POST.get('email', usuario.email)
        usuario.save()
        messages.success(request, f"✅ Usuario {usuario.username} actualizado correctamente.")
        return redirect('gestionar_usuarios')

    return render(request, 'administrador/editar_usuario.html', {'usuario': usuario})

@login_required
@staff_member_required
def eliminar_usuario(request, usuario_id):
    """Permite a los administradores eliminar usuarios con confirmación."""
    usuario = get_object_or_404(Usuario, id=usuario_id)

    if request.method == 'POST':
        # Confirmar eliminación
        try:
            usuario.delete()
            messages.success(request, f"❌ Usuario {usuario.username} eliminado correctamente.")
        except Exception as e:
            messages.error(request, f"⚠️ Error al eliminar el usuario: {str(e)}")
        return redirect('gestionar_usuarios')  # Redirige a la lista actualizada

    # Mostrar página de confirmación
    return render(request, 'administrador/eliminar_usuario.html', {'usuario': usuario})

@login_required
@staff_member_required
def editar_especialista(request, especialista_id):
    """Permite a los administradores editar especialistas con seguridad y mejor rendimiento."""
    especialista = get_object_or_404(Usuario, id=especialista_id, es_especialista=True)

    # Obtener todas las especialidades disponibles
    especialidades = Especialidad.objects.all()

    if request.method == 'POST':
        # Validar y actualizar los datos del especialista
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        especialidad_id = request.POST.get('especialidad')

        # Validar que los campos no estén vacíos
        if not username or not email:
            messages.error(request, "⚠️ El nombre y el correo electrónico son obligatorios.")
        elif not Especialidad.objects.filter(id=especialidad_id).exists():
            messages.error(request, "⚠️ La especialidad seleccionada no es válida.")
        else:
            # Actualizar los datos del especialista
            especialista.username = username
            especialista.email = email
            especialista.especialidad = Especialidad.objects.get(id=especialidad_id)
            especialista.save()
            messages.success(request, f"✅ Especialista {especialista.username} actualizado correctamente.")
            return redirect('gestionar_especialistas')

    return render(request, 'administrador/editar_especialista.html', {
        'especialista': especialista,
        'especialidades': especialidades
    })

@login_required
@staff_member_required
def eliminar_especialista(request, especialista_id):
    """Permite a los administradores eliminar especialistas con validación de permisos y confirmación."""
    especialista = get_object_or_404(Usuario, id=especialista_id, es_especialista=True)

    if request.method == 'POST':
        # Confirmar eliminación
        try:
            especialista.delete()
            messages.success(request, f"❌ Especialista {especialista.username} eliminado correctamente.")
        except Exception as e:
            messages.error(request, f"⚠️ Error al eliminar el especialista: {str(e)}")
        return redirect('gestionar_especialistas')  # Redirige a la lista actualizada

    # Mostrar página de confirmación
    return render(request, 'administrador/eliminar_especialista.html', {'especialista': especialista})

@login_required
def gestionar_disponibilidad(request):
    especialistas = Usuario.objects.filter(es_especialista=True)
    disponibilidades = Disponibilidad.objects.all()

    if request.method == "POST":
        especialista_id = request.POST.get("especialista")
        fecha = request.POST.get("fecha")
        hora_inicio = request.POST.get("hora_inicio")
        hora_fin = request.POST.get("hora_fin")

        especialista = Usuario.objects.get(id=especialista_id)
        Disponibilidad.objects.create(
            especialista=especialista,
            fecha=fecha,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            disponible=True
        )
        messages.success(request, "Disponibilidad añadida correctamente.")
        return redirect("gestionar_disponibilidad")

    return render(request, "administrador/disponibilidad.html", {
        "especialistas": especialistas,
        "disponibilidades": disponibilidades,
    })

@login_required
def añadir_disponibilidad(request):
    if request.method == 'POST':
        form = DisponibilidadForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Disponibilidad añadida correctamente.')
            return redirect('gestionar_disponibilidad')
        else:
            # Imprime los errores del formulario en la consola
            print(form.errors)
            messages.error(request, f"Error al añadir la disponibilidad: {form.errors}")
    else:
        form = DisponibilidadForm()

    # Obtener todos los especialistas
    especialistas = Usuario.objects.filter(es_especialista=True)

    return render(request, 'administrador/añadir_disponibilidad.html', {
        'form': form,
        'especialistas': especialistas
    })



def obtener_disponibilidad(request, especialista_id):
    disponibilidades = Disponibilidad.objects.filter(especialista_id=especialista_id, disponible=True)
    data = [
        {
            "id": disponibilidad.id,
            "fecha": disponibilidad.fecha.strftime("%Y-%m-%d"),
            "hora_inicio": disponibilidad.hora_inicio.strftime("%H:%M"),
            "hora_fin": disponibilidad.hora_fin.strftime("%H:%M"),
        }
        for disponibilidad in disponibilidades
    ]
    return JsonResponse(data, safe=False)

@login_required
def registrar_cita(request):
    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            usuario_id = request.POST.get('usuario')
            usuario = Usuario.objects.get(id=usuario_id)
            cita = form.save(commit=False)
            cita.usuario = usuario
            cita.save()
            return redirect('gestionar_citas')
    else:
        form = CitaForm()
    
    usuarios = Usuario.objects.all()
    especialidades = Especialidad.objects.all()
    return render(request, 'administrador/registrar_cita.html', {
        'form': form,
        'usuarios': usuarios,
        'especialidades': especialidades,
    })

class CustomPasswordResetView(PasswordResetView):
    def form_valid(self, form):
        email = form.cleaned_data.get('email')
        if not User.objects.filter(email=email).exists():
            # Si el correo no está registrado, muestra un mensaje de error
            messages.error(self.request, "⚠️ El correo ingresado no está registrado.")
            return self.form_invalid(form)  # Devuelve el formulario con el error
        return super().form_valid(form)


@login_required
@staff_member_required
def editar_disponibilidad(request, disponibilidad_id):
    """Permite a los administradores editar una disponibilidad existente."""
    disponibilidad = get_object_or_404(Disponibilidad, id=disponibilidad_id)

    if request.method == 'POST':
        # Obtener los datos del formulario
        fecha = request.POST.get('fecha')
        hora_inicio = request.POST.get('hora_inicio')
        hora_fin = request.POST.get('hora_fin')
        disponible = request.POST.get('disponible') == 'on'

        # Validar y actualizar los datos
        try:
            disponibilidad.fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
            disponibilidad.hora_inicio = datetime.strptime(hora_inicio, '%H:%M').time()
            disponibilidad.hora_fin = datetime.strptime(hora_fin, '%H:%M').time()
            disponibilidad.disponible = disponible
            disponibilidad.save()
            messages.success(request, "✅ Disponibilidad actualizada correctamente.")
            return redirect('gestionar_disponibilidad')
        except Exception as e:
            messages.error(request, f"⚠️ Error al actualizar la disponibilidad: {str(e)}")

    return render(request, 'administrador/editar_disponibilidad.html', {
        'disponibilidad': disponibilidad
    })