from django.contrib import admin
from .models import Usuario, Especialidad, Cita, Blog

admin.site.register(Usuario)
admin.site.register(Especialidad)
admin.site.register(Cita)
admin.site.register(Blog)