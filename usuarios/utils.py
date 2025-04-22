from django.core.mail import send_mail
from django.conf import settings

def enviar_notificacion_administrador(cita):
    asunto = f"Nuevo Registro de Cita Pendiente - {cita.id}"
    mensaje = (
        f"Se ha registrado una nueva cita en el sistema:\n\n"
        f"Usuario: {cita.usuario.username}\n"
        f"Especialidad: {cita.especialidad.nombre}\n"
        f"Fecha y Hora: {cita.fecha_hora}\n\n"
        f"Por favor, revisa el sistema para aceptarla o rechazarla."
    )
    destinatarios = ['admin@gmail.com'] 
    send_mail(asunto, mensaje, settings.EMAIL_HOST_USER, destinatarios)
