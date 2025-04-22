
# class SecurityBehavior(TaskSet):
#     # Prueba de acceso no autorizado
#     @task(1)
#     def acceso_no_autorizado(self):
#         self.client.get("/administrador/citas/", name="Acceso no autorizado")  # Intentar acceder sin autenticación

#     # Prueba de acceso a recursos restringidos
#     @task(1)
#     def acceso_restringido(self):
#         self.client.get("/usuarios/citas/9999/", name="Acceso a recurso restringido")  # Intentar acceder a un recurso no permitido

#     # Prueba de inicio de sesión fallido
#     @task(1)
#     def inicio_sesion_fallido(self):
#         self.client.post("/login/", {"username": "usuario_invalido", "password": "contraseña_incorrecta"}, name="Inicio de sesión fallido")

# class SecurityUser(HttpUser):
#     tasks = [SecurityBehavior]
#     min_wait = 1000  # Tiempo mínimo entre solicitudes (ms)
#     max_wait = 2000  # Tiempo máximo entre solicitudes (ms)

from locust import HttpUser, TaskSet, task

class UserBehavior(TaskSet):
    @task(1)
    def profile(self):
        self.client.get("/profile/")  # Ruta correcta

    @task(2)
    def gestionar_citas_admin(self):
        self.client.get("/administrador/citas/")  # Ruta correcta

    @task(1)
    def panel_administrador(self):
        self.client.get("/administrador/panel/")  # Corrige esta ruta si es necesario

    @task(1)
    def reservar_cita(self):
        self.client.get("/reservar_cita/")  # Ruta correcta

    @task(1)
    def usuario_view(self):
        self.client.get("/usuario/")  # Ruta correcta

    @task(1)
    def mensajes_recibidos(self):
        self.client.get("/mensajes_recibidos/")  # Muestra los mensajes recibidos por el usuario

    @task(1)
    def gestionar_testimonios(self):
        self.client.get("/administrador/testimonios/")  # Gestión de testimonios por el administrador

    @task(1)
    def gestionar_blog(self):
        self.client.get("/administrador/blogs/")  # Gestión de blogs por el administrador

    @task(1)
    def blog_detalle(self):
        self.client.get("/blog/3/")  # Detalle de un blog específico (ID 1 como ejemplo)

    @task(1)
    def gestionar_especialistas(self):
        self.client.get("/administrador/especialistas/")  # Gestión de especialistas por el administrador

    @task(1)
    def gestionar_disponibilidad(self):
        self.client.get("/administrador/gestionar_disponibilidad/")  # Gestión de disponibilidad de especialistas


class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    min_wait = 1000  # Tiempo mínimo entre solicitudes (ms)
    max_wait = 2000  # Tiempo máximo entre solicitudes (ms)