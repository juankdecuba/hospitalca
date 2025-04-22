from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import is_naive, make_naive, now
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.utils.timezone import make_aware, now
from django.dispatch import receiver
from django.apps import apps


class Especialidad(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre
    

class Usuario(AbstractUser):
    es_admin = models.BooleanField(default=False)
    es_especialista = models.BooleanField(default=False)
    especialidad = models.ForeignKey(
        Especialidad,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='especialistas'
    )
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        related_name="usuario_set",
        related_query_name="usuario",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        related_name="usuario_set",
        related_query_name="usuario",
    )
    
    class Meta:
        db_table = 'usuarios_usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    @property
    def profile(self):
        """Propiedad para acceder al perfil asociado"""
        Profile = apps.get_model('usuarios.Profile')
        profile, created = Profile.objects.get_or_create(user=self)
        return profile

class Especialista(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='especialista')
    especialidad = models.ForeignKey(Especialidad, on_delete=models.SET_NULL, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)  # Campo que causa el error

    def __str__(self):
        return self.usuario.username
    
class Profile(models.Model):
    user = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='user_profile'
    )
    bio = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'usuarios_profile'
    
    def __str__(self):
        return f"Perfil de {self.user.username}"

class Cita(models.Model):
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='citas_paciente'
    )
    especialista = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='citas_especialista'
    )
    especialidad = models.ForeignKey(
        Especialidad,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    fecha_hora = models.DateTimeField()
    descripcion = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=[
            ('pendiente', 'Pendiente'),
            ('aceptada', 'Aceptada'),
            ('rechazada', 'Rechazada'),
            ('cancelada', 'Cancelada'),
            ('completada', 'Completada'),
        ],
        default='pendiente',
    )
    motivo_rechazo = models.TextField(blank=True, null=True)  # Campo para el motivo del rechazo

    class Meta:
        ordering = ['-fecha_hora']
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'

    def __str__(self):
        return f"Cita {self.id} - {self.usuario.username} ({self.estado})"

    def clean(self):
        """Validaciones adicionales antes de guardar"""
        if self.fecha_hora:
            # Asegúrate de que ambos datetime sean del mismo tipo (naive o aware)
            current_time = now()
            if is_naive(self.fecha_hora):
                current_time = make_naive(current_time)

            if self.fecha_hora < current_time:
                raise ValidationError("La fecha y hora no pueden ser en el pasado.")
        
        if self.especialidad and self.especialista and self.especialista.especialidad != self.especialidad:
            raise ValidationError('El especialista no pertenece a la especialidad seleccionada.')

    def save(self, *args, **kwargs):
        """Validación antes de guardar"""
        self.clean()
        super().save(*args, **kwargs)



class Testimonio(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="testimonios"
    )
    comentario = models.TextField(verbose_name="Comentario del usuario")  # Descripción más clara
    experiencia = models.CharField(
        max_length=10,
        choices=[
            ('excelente', 'Excelente'),
            ('buena', 'Buena'),
            ('regular', 'Regular'),
            ('mala', 'Mala'),
        ],
        default='buena',
        verbose_name="Nivel de experiencia"
    )
    fecha_publicacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de publicación")
    aprobado = models.BooleanField(default=False, verbose_name="Aprobado por el administrador")
    destacado = models.BooleanField(default=False, verbose_name="Destacar en la página principal")  # Nuevo campo

    class Meta:
        ordering = ['-fecha_publicacion']  # Ordenar por fecha de publicación descendente
        verbose_name = "Testimonio"
        verbose_name_plural = "Testimonios"

    def __str__(self):
        return f'Testimonio de {self.usuario.username} - {self.get_experiencia_display()}'

class Mensaje(models.Model):
    remitente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mensajes_enviados"
    )
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mensajes_recibidos"
    )
    contenido = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)  # Nuevo campo para rastrear si el mensaje ha sido leído

    def __str__(self):
        return f"Mensaje de {self.remitente.username} para {self.destinatario.username} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"
    
    
class Blog(models.Model):
    titulo = models.CharField(max_length=200)
    resumen = models.TextField()
    contenido = models.TextField()
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    imagen = models.ImageField(upload_to='blog_images/', blank=True, null=True)
    aprobado = models.BooleanField(default=False)  # Nuevo campo para aprobación

    def __str__(self):
        return self.titulo
    

class Disponibilidad(models.Model):
    especialista = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='disponibilidades'
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    disponible = models.BooleanField(default=True)

    def clean(self):
        # Validar que la hora de inicio sea anterior a la hora de fin
        if self.hora_inicio >= self.hora_fin:
            raise ValidationError("La hora de inicio debe ser anterior a la hora de fin.")
        
        # Validar que la fecha no sea en el pasado
        from datetime import date
        if self.fecha < date.today():
            raise ValidationError("La fecha no puede ser en el pasado.")

    def save(self, *args, **kwargs):
        # Llama a la validación antes de guardar
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.especialista.username} - {self.fecha} ({self.hora_inicio} - {self.hora_fin})"
