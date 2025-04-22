import pytest
from django.utils.timezone import now, timedelta
from usuarios.models import (
    Especialidad, Usuario, Especialista, Profile, Cita, Testimonio, Mensaje, Blog
)
from django.core.exceptions import ValidationError

@pytest.mark.django_db
def test_especialidad_str():
    especialidad = Especialidad.objects.create(nombre="Cardiología")
    assert str(especialidad) == "Cardiología"

@pytest.mark.django_db
def test_usuario_profile_creation():
    usuario = Usuario.objects.create(username="testuser", password="12345")
    assert usuario.profile  # Verifica que el perfil se crea automáticamente

@pytest.mark.django_db
def test_especialista_str():
    especialidad = Especialidad.objects.create(nombre="Dermatología")
    usuario = Usuario.objects.create(username="especialista", password="12345", es_especialista=True)
    especialista = Especialista.objects.create(usuario=usuario, email="especialista@example.com", especialidad=especialidad)
    assert str(especialista) == "especialista"

@pytest.mark.django_db
def test_profile_str():
    usuario = Usuario.objects.create(username="testuser", password="12345")
    profile = Profile.objects.create(user=usuario, bio="Bio de prueba")
    assert str(profile) == f"Perfil de {usuario.username}"

@pytest.mark.django_db
def test_cita_creation():
    especialidad = Especialidad.objects.create(nombre="Cardiología")
    usuario = Usuario.objects.create(username="paciente", password="12345")
    especialista = Usuario.objects.create(username="especialista", password="12345", es_especialista=True, especialidad=especialidad)
    fecha_hora = now() + timedelta(days=1)
    cita = Cita.objects.create(
        usuario=usuario,
        especialista=especialista,
        especialidad=especialidad,
        fecha_hora=fecha_hora,
        descripcion="Consulta general"
    )
    assert str(cita) == f"Cita {cita.id} - {usuario.username} (pendiente)"

@pytest.mark.django_db
def test_cita_clean_fecha_pasada():
    especialidad = Especialidad.objects.create(nombre="Pediatría")
    usuario = Usuario.objects.create(username="paciente", password="12345")
    especialista = Usuario.objects.create(username="especialista", password="12345", es_especialista=True, especialidad=especialidad)
    fecha_hora = now() - timedelta(days=1)  # Fecha pasada
    cita = Cita(
        usuario=usuario,
        especialista=especialista,
        especialidad=especialidad,
        fecha_hora=fecha_hora,
        descripcion="Consulta general"
    )
    with pytest.raises(ValidationError) as excinfo:
        cita.clean()  # Llama al método clean del modelo
    assert "La fecha y hora no pueden ser en el pasado." in str(excinfo.value)

@pytest.mark.django_db
def test_testimonio_creation():
    usuario = Usuario.objects.create(username="testuser", password="12345")
    testimonio = Testimonio.objects.create(
        usuario=usuario,
        comentario="¡Excelente servicio!",
        experiencia="excelente"
    )
    assert str(testimonio) == f"Testimonio de {usuario.username} - Excelente"

@pytest.mark.django_db
def test_mensaje_creation():
    remitente = Usuario.objects.create(username="remitente", password="12345")
    mensaje = Mensaje.objects.create(
        remitente=remitente,
        contenido="Hola, este es un mensaje de prueba."
    )
    assert str(mensaje).startswith(f"Mensaje de {remitente.username} - ")

@pytest.mark.django_db
def test_blog_creation():
    blog = Blog.objects.create(
        titulo="Título del Blog",
        resumen="Resumen del blog",
        contenido="Contenido del blog"
    )
    assert str(blog) == "Título del Blog"