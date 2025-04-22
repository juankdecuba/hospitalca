from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from usuarios.models import Usuario, Cita, Especialidad, Blog, Testimonio, Mensaje
import time
from datetime import datetime
from django.utils.timezone import make_aware


class ViewsTestCase(TestCase):
    def setUp(self):
        # Configuración inicial para las pruebas
        self.client = Client()

        # Crear usuarios
        self.admin_user = Usuario.objects.create_superuser(username="admin", password="admin123", email="admin@example.com")
        self.especialista_user = Usuario.objects.create_user(username="especialista", password="especialista123", email="especialista@example.com", es_especialista=True)
        self.normal_user = Usuario.objects.create_user(username="usuario", password="usuario123", email="usuario@example.com")

        # Crear datos adicionales
        self.especialidad = Especialidad.objects.create(nombre="Cardiología")
        self.blog = Blog.objects.create(titulo="Blog de prueba", contenido="Contenido de prueba", aprobado=True)
        self.testimonio = Testimonio.objects.create(usuario=self.normal_user, experiencia="Buena", comentario="Muy buen servicio", aprobado=True)

        # Convertir fecha_hora a datetime aware
        fecha_hora = make_aware(datetime.strptime("2025-04-10 10:00:00", "%Y-%m-%d %H:%M:%S"))
        self.cita = Cita.objects.create(usuario=self.normal_user, especialista=self.especialista_user, fecha_hora=fecha_hora, estado="pendiente")
    
    def test_login_view(self):
        response = self.client.post(reverse('login'), {'username': 'usuario', 'password': 'usuario123'})
        self.assertEqual(response.status_code, 302)  # Redirección después de iniciar sesión
        self.assertRedirects(response, reverse('usuario'))  # Redirige al panel de usuario

    def test_register_view(self):
        response = self.client.post(reverse('register'), {'username': 'nuevo_usuario', 'password': 'Password123!', 'email': 'nuevo@example.com'})
        self.assertEqual(response.status_code, 302)  # Redirección después de registrar
        self.assertTrue(Usuario.objects.filter(username="nuevo_usuario").exists())

    def test_panel_administrador(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse('administrador'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Usuarios")

    def test_gestionar_especialistas(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse('gestionar_especialistas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Especialistas")

    def test_gestionar_citas_admin(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse('gestionar_citas_admin'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h3>Citas Pendientes</h3>", html=True)

    def test_reservar_cita(self):
        self.client.login(username="usuario", password="usuario123")
        response = self.client.post(reverse('reservar_cita'), {
            'especialista': self.especialista_user.id,
            'fecha_hora': "2025-04-15 10:00:00"
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Cita.objects.filter(usuario=self.normal_user, especialista=self.especialista_user).exists())

    def test_gestionar_blog(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.get(reverse('gestionar_blog'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Blog de prueba")

    def test_aprobar_blog(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.post(reverse('aprobar_blog', args=[self.blog.id]))
        self.assertEqual(response.status_code, 302)  # Redirección después de aprobar
        self.blog.refresh_from_db()
        self.assertFalse(self.blog.aprobado)  # Cambia el estado de aprobado

    def test_agregar_testimonio(self):
        self.client.login(username="usuario", password="usuario123")
        response = self.client.post(reverse('agregar_testimonio'), {
            'comentario': "Muy buen servicio",
            'experiencia': "excelente"
        })
        self.assertEqual(response.status_code, 302)  # Redirección después de agregar
        self.assertTrue(Testimonio.objects.filter(usuario=self.normal_user, experiencia="excelente").exists())

    def test_mensajes_recibidos(self):
        Mensaje.objects.create(remitente=self.admin_user, destinatario=self.normal_user, contenido="Mensaje de prueba")
        self.client.login(username="usuario", password="usuario123")
        response = self.client.get(reverse('mensajes_recibidos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mensaje de prueba")

    def test_editar_usuario(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.post(reverse('editar_usuario', args=[self.normal_user.id]), {
            'username': "usuario_editado",
            'email': "editado@example.com"
        })
        self.assertEqual(response.status_code, 302)  # Redirección después de editar
        self.normal_user.refresh_from_db()
        self.assertEqual(self.normal_user.username, "usuario_editado")

    def test_eliminar_usuario(self):
        self.client.login(username="admin", password="admin123")
        response = self.client.post(reverse('eliminar_usuario', args=[self.normal_user.id]))
        self.assertEqual(response.status_code, 302)  # Redirección después de eliminar
        self.assertFalse(Usuario.objects.filter(id=self.normal_user.id).exists())




class PerformanceTestCase(TestCase):
    def setUp(self):
        # Configuración inicial para las pruebas
        self.client = Client()

        # Crear usuarios
        self.admin_user = Usuario.objects.create_superuser(username="admin", password="admin123", email="admin@example.com")
        self.normal_user = Usuario.objects.create_user(username="usuario", password="usuario123", email="usuario@example.com")

        # Crear datos adicionales
        self.especialista_user = Usuario.objects.create_user(username="especialista", password="especialista123", email="especialista@example.com", es_especialista=True)
        self.especialidad = Especialidad.objects.create(nombre="Cardiología")
        for i in range(100):  # Crear 100 citas para probar rendimiento con datos grandes
            Cita.objects.create(
                usuario=self.normal_user,
                especialista=self.especialista_user,
                fecha_hora=make_aware(datetime.strptime(f"2025-04-{10 + i % 20} 10:00:00", "%Y-%m-%d %H:%M:%S")),
                estado="pendiente"
            )

    def test_rendimiento_vistas_publicas(self):
        """Prueba el rendimiento de vistas públicas (sin autenticación)"""
        urls = [
            reverse('login'),
            reverse('register'),
        ]
        for url in urls:
            start_time = time.time()
            response = self.client.get(url)
            end_time = time.time()
            self.assertEqual(response.status_code, 200)
            self.assertLess(end_time - start_time, 1, f"La vista {url} tardó demasiado en responder.")

    def test_rendimiento_vistas_privadas(self):
        """Prueba el rendimiento de vistas privadas (requieren autenticación)"""
        self.client.login(username="usuario", password="usuario123")
        urls = [
            reverse('profile'),
            reverse('reservar_cita'),
        ]
        for url in urls:
            start_time = time.time()
            response = self.client.get(url)
            end_time = time.time()
            self.assertEqual(response.status_code, 200)
            self.assertLess(end_time - start_time, 1, f"La vista {url} tardó demasiado en responder.")

    def test_rendimiento_vistas_administrativas(self):
        """Prueba el rendimiento de vistas administrativas"""
        self.client.login(username="admin", password="admin123")
        urls = [
            reverse('administrador'),
            reverse('gestionar_citas_admin'),
            reverse('gestionar_blog'),
        ]
        for url in urls:
            start_time = time.time()
            response = self.client.get(url)
            end_time = time.time()
            self.assertEqual(response.status_code, 200)
            self.assertLess(end_time - start_time, 1, f"La vista {url} tardó demasiado en responder.")

    def test_rendimiento_post_reservar_cita(self):
        """Prueba el rendimiento de la vista de reservar cita con POST"""
        self.client.login(username="usuario", password="usuario123")
        start_time = time.time()
        response = self.client.post(reverse('reservar_cita'), {
            'especialista': self.especialista_user.id,
            'fecha_hora': "2025-04-15 10:00:00"
        })
        end_time = time.time()
        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 1, "La vista reservar_cita tardó demasiado en responder.")  

    def medir_tiempo_respuesta(self, url, metodo="get", datos=None):
        start_time = time.time()
        if metodo == "get":
            response = self.client.get(url)
        elif metodo == "post":
            response = self.client.post(url, datos)
        end_time = time.time()
        return response, end_time - start_time       
    