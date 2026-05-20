"""URLs raiz — Agenda Hora a Hora."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Autenticação JWT
    path('api/auth/', include('apps.tenants.auth_urls')),

    # Config pública do tenant
    path('api/tenant/', include('apps.tenants.urls')),

    # Apps de negócio
    path('api/', include('apps.agendas.urls')),
    path('api/', include('apps.tarefas.urls')),
    path('api/', include('apps.setores.urls')),
    path('api/', include('apps.justificativas.urls')),
    path('api/', include('apps.notificacoes.urls')),
    path('api/', include('apps.feriados.urls')),
    path('api/', include('apps.templates_agenda.urls')),
    path('api/', include('apps.relatorios.urls')),

    # Admin (BUs, usuários)
    path('api/admin/', include('apps.usuarios.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
