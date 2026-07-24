from datetime import timedelta
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from apps.solicitacoes.models import Solicitacao


class Command(BaseCommand):
    help = "Envia pesquisas de satisfação"

    def handle(self, *args, **kwargs):

        limite = timezone.now() - timedelta(hours=48)

        solicitacoes = Solicitacao.objects.filter(
            status="APROVADO",
            pesquisa_enviada=False,
            data_evento__lte=limite.date()
        )

        for s in solicitacoes:

            link = (
                f"https://siev95.com.br/"
                f"pesquisa/{s.pesquisa_token}/"
            )

            mensagem = f"""
Olá {s.solicitante},

Esperamos que seu evento tenha ocorrido da melhor forma possível.

Sua opinião é muito importante para nós.

Avalie nosso atendimento acessando:

{link}

Muito obrigado.

95ª CIPM
Polícia Militar da Bahia
"""

            try:

                send_mail(
                    "Pesquisa de Satisfação - SiEv",
                    mensagem,
                    settings.DEFAULT_FROM_EMAIL,
                    [s.email],
                    fail_silently=False
                )

                s.pesquisa_enviada = True
                s.data_envio_pesquisa = timezone.now()
                s.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Pesquisa enviada para {s.email}"
                    )
                )

            except Exception as erro:

                self.stdout.write(
                    self.style.ERROR(str(erro))
                )