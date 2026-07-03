from django.contrib import admin

from django.utils import timezone

from .models import Solicitacao

from .utils import gerar_pdf_autorizacao


@admin.register(Solicitacao)
class SolicitacaoAdmin(admin.ModelAdmin):

    list_display = (
        'protocolo',
        'nome_evento',
        'solicitante',
        'data_evento',
        'status',
    )

    search_fields = (
        'protocolo',
        'nome_evento',
        'solicitante',
    )

    list_filter = (
        'status',
        'data_evento',
    )

    actions = ['aprovar_solicitacao']

    def aprovar_solicitacao(
        self,
        request,
        queryset
    ):

        for solicitacao in queryset:

            solicitacao.status = 'APROVADA'

            solicitacao.assinado_por = (
                request.user.get_full_name()
                or request.user.username
            )

            solicitacao.data_assinatura = timezone.now()

            nome_pdf = gerar_pdf_autorizacao(
                solicitacao
            )

            solicitacao.pdf_autorizacao = (
                f'autorizacoes/{nome_pdf}'
            )

            solicitacao.save()

    aprovar_solicitacao.short_description = (
        'Aprovar solicitações'
    )