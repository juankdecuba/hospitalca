import pytest
from django.utils.timezone import now, timedelta
import warnings
warnings.filterwarnings("ignore", category=pytest.PytestCollectionWarning)
from usuarios.forms import (
    EspecialistaCreationForm,
    CitaForm,
    TestimonioForm,
    BlogForm
)
from usuarios.models import Especialidad, Usuario

@pytest.mark.django_db
def test_especialista_creation_form_valid():
    especialidad = Especialidad.objects.create(nombre="Cardiología")
    form_data = {
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'password123',
        'especialidad': especialidad.id
    }
    form = EspecialistaCreationForm(data=form_data)
    assert form.is_valid()

@pytest.mark.django_db
def test_especialista_creation_form_invalid():
    form_data = {
        'username': '',  # Campo vacío
        'email': 'invalid-email',
        'password': 'password123',
        'especialidad': None  # Sin especialidad
    }
    form = EspecialistaCreationForm(data=form_data)
    assert not form.is_valid()
    assert 'username' in form.errors
    assert 'email' in form.errors
    assert 'especialidad' in form.errors

@pytest.mark.django_db
def test_cita_form_valid():
    especialidad = Especialidad.objects.create(nombre="Dermatología")
    usuario = Usuario.objects.create(username="testuser", password="12345")
    fecha_hora = now() + timedelta(days=1)  # Fecha futura
    form_data = {
        'especialidad': especialidad.id,
        'especialista': usuario.id,
        'fecha_hora': fecha_hora,
        'descripcion': 'Consulta general'
    }
    form = CitaForm(data=form_data)
    assert form.is_valid()

@pytest.mark.django_db
def test_cita_form_invalid_past_date():
    especialidad = Especialidad.objects.create(nombre="Pediatría")
    usuario = Usuario.objects.create(username="testuser", password="12345")
    fecha_hora = now() - timedelta(days=1)  # Fecha pasada
    form_data = {
        'especialidad': especialidad.id,
        'especialista': usuario.id,
        'fecha_hora': fecha_hora,
        'descripcion': 'Consulta general'
    }
    form = CitaForm(data=form_data)
    assert not form.is_valid()
    assert 'fecha_hora' in form.errors

@pytest.mark.django_db
def test_testimonio_form_valid():
    form_data = {
        'comentario': '¡Excelente servicio!',
        'experiencia': 'excelente'
    }
    form = TestimonioForm(data=form_data)
    assert form.is_valid()

@pytest.mark.django_db
def test_testimonio_form_invalid():
    form_data = {
        'comentario': '',  # Campo vacío
        'experiencia': 'invalida'  # Valor no permitido
    }
    form = TestimonioForm(data=form_data)
    assert not form.is_valid()
    assert 'comentario' in form.errors
    assert 'experiencia' in form.errors

@pytest.mark.django_db
def test_blog_form_valid():
    form_data = {
        'titulo': 'Nuevo Blog',
        'resumen': 'Este es un resumen del blog.',
        'contenido': 'Contenido detallado del blog.',
        'imagen': None  # Imagen opcional
    }
    form = BlogForm(data=form_data)
    assert form.is_valid()

@pytest.mark.django_db
def test_blog_form_invalid():
    form_data = {
        'titulo': '',  # Campo vacío
        'resumen': '',
        'contenido': ''
    }
    form = BlogForm(data=form_data)
    assert not form.is_valid()
    assert 'titulo' in form.errors
    assert 'resumen' in form.errors
    assert 'contenido' in form.errors