from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from apps.solicitacoes.views import (
    home,
    nova_solicitacao,
    minhas_solicitacoes,
    consultar_protocolo,
    dashboard_operacional,
    verificar_autenticidade,
    alterar_status,
    login_gestao,
    logout_gestao,
    painel_gestao,
    baixar_processo,
    abrir_documento_solicitacao,
    documentos_solicitacao,
    aprovar_solicitacao,
    gerar_opo,
    listar_pendentes_opo,
    visualizar_documentos,
    abrir_documento_solicitacao,
    opos_geradas,
    detalhe_opo,
)

urlpatterns = [

    path('admin/', admin.site.urls),
    
    path(
        "documentos/<int:id>/",
        visualizar_documentos,
        name="visualizar_documentos"
    ),
        

    path('', home, name='home'),

    path('gestao/', login_gestao, name='login_gestao'),

    path('logout/', logout_gestao, name='logout_gestao'),
    
    path(
        "aprovar/<int:id>/",
        aprovar_solicitacao,
        name="aprovar_solicitacao"
    ),

    path(
        "arquivo-documento/<int:id>/<str:tipo>/",
        abrir_documento_solicitacao,
        name="abrir_documento_solicitacao"
    ),

    path(
        "opo/<int:id>/",
        gerar_opo,
        name="gerar_opo"
    ),

    path(
        "aprovacoes/",
        listar_pendentes_opo,
        name="listar_pendentes_opo"
    ),

    path(
        "documentos/<int:id>/",
        documentos_solicitacao,
        name="documentos_solicitacao"
    ),
    path(
        "gestao/opos-geradas/",
        opos_geradas,
        name="opos_geradas"
    ),

    path(
        "gestao/opo/<int:id>/detalhes/",
        detalhe_opo,
        name="detalhe_opo"
    ),
    path(
        "documento/<int:id>/<str:tipo>/",
        abrir_documento_solicitacao,
        name="abrir_documento_solicitacao"
    ),

    path(
        'painel/',
        painel_gestao,
        name='painel_gestao'
    ),

    path(
        'consultar/',
        consultar_protocolo,
        name='consultar_protocolo'
    ),

    path(
        'nova/',
        nova_solicitacao,
        name='nova_solicitacao'
    ),

    path(
        'minhas/',
        minhas_solicitacoes,
        name='minhas_solicitacoes'
    ),

    path(
        'dashboard/',
        dashboard_operacional,
        name='dashboard_operacional'
    ),

    path(
        'verificar/<str:protocolo>/',
        verificar_autenticidade,
        name='verificar_autenticidade'
    ),

    path(
        'alterar-status/<int:id>/<str:status>/',
        alterar_status,
        name='alterar_status'
    ),

    
    path(
        "processo/<int:id>/zip/",
        baixar_processo,
        name="baixar_processo"
    ),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

