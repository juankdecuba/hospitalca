from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from usuarios.models import Especialidad

class Command(BaseCommand):
    help = 'Create default specialty and specialist'

    def handle(self, *args, **kwargs):
        # Crear especialidad por defecto
        especialidad, created = Especialidad.objects.get_or_create(nombre='Especialidad X')
        if created:
            self.stdout.write(self.style.SUCCESS('Especialidad creada con éxito: Especialidad X'))
        else:
            self.stdout.write(self.style.WARNING('Especialidad ya existía: Especialidad X'))

        # Crear especialista por defecto
        Usuario = get_user_model()
        especialista, created = Usuario.objects.get_or_create(username='especialista1', defaults={
            'email': 'especialista@example.com',
            'especialidad': especialidad,
            'es_especialista': True
        })

        if created:
            self.stdout.write(self.style.SUCCESS('Especialista creado con éxito: especialista1'))
        else:
            self.stdout.write(self.style.WARNING('Especialista ya existía: especialista1'))
        
        # Establecer la contraseña del especialista
        especialista.set_password('password123')
        especialista.save()
