from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.db import models
from django.contrib.auth.models import User
from .models import Blog, Usuario, Especialidad, Cita, Testimonio,Especialista,Disponibilidad
    
def save(self, commit=True):
    user = super().save(commit=False)
    user.es_especialista = True
    if commit:
        user.save()
    return user

class CitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['especialidad', 'especialista', 'fecha_hora', 'descripcion']
        widgets = {
            'fecha_hora': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean_fecha_hora(self):
        """Validación para evitar fechas pasadas"""
        fecha_hora = self.cleaned_data.get('fecha_hora')
        if fecha_hora and fecha_hora < now():
            raise ValidationError("No puedes reservar una cita para días pasados.")
        return fecha_hora

class TestimonioForm(forms.ModelForm):
    class Meta:
        model = Testimonio
        fields = ['comentario', 'experiencia']


class EspecialistaCreationForm(forms.ModelForm):
    username = forms.CharField(max_length=100, label="Nombre de usuario")
    email = forms.EmailField(label="Correo electrónico")
    password = forms.CharField(widget=forms.PasswordInput, label="Contraseña")
    especialidad = forms.ModelChoiceField(queryset=Especialidad.objects.all(), label="Especialidad")

    class Meta:
        model = Especialista
        fields = ['especialidad']  # Solo el campo relacionado al modelo Especialista

    def clean_username(self):
        """Validar que el nombre de usuario no exista ya en la base de datos."""
        username = self.cleaned_data.get('username')
        if Usuario.objects.filter(username=username).exists():
            raise forms.ValidationError("El nombre de usuario ya está en uso. Por favor, elige otro.")
        return username

    def clean_email(self):
        """Validar que el correo electrónico no exista ya en la base de datos."""
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("El correo electrónico ya está en uso. Por favor, utiliza otro.")
        return email

    def save(self, commit=True): 
    # Crear el usuario relacionado al especialista
        usuario = Usuario.objects.create_user(
        username=self.cleaned_data['username'],
        email=self.cleaned_data['email'],
        password=self.cleaned_data['password']
    )
        usuario.es_especialista = True  # Marcar al usuario como especialista
        usuario.save()

        especialista = super().save(commit=False)
        especialista.usuario = usuario
        if commit:
            especialista.save()
        return especialista

class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['titulo', 'resumen', 'contenido', 'imagen']    

     
class DisponibilidadForm(forms.ModelForm):
    class Meta:
        model = Disponibilidad
        fields = ['especialista', 'fecha', 'hora_inicio', 'hora_fin', 'disponible']