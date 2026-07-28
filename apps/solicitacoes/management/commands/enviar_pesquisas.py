from datetime import datetime, timedelta
import secrets
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.solicitacoes.models import Solicitacao


class Command(BaseCommand):
    help = "Envia pesquisas de satisfação"

    def handle(self, *args, **kwargs):
        self.stdout.write("INICIOU O COMANDO")

        agora = timezone.now()
        enviados = 0

        solicitacoes = Solicitacao.objects.filter(
            status="APROVADO",
            pesquisa_enviada=False
        )

        for s in solicitacoes:

            try:
                # Gera o token caso não exista
                if not s.pesquisa_token:
                    s.pesquisa_token = secrets.token_urlsafe(32)

                # Data/hora de início e término
                inicio = datetime.combine(s.data_evento, s.hora_inicio)
                fim = datetime.combine(s.data_evento, s.hora_fim)

                # Evento terminou no dia seguinte
                if fim <= inicio:
                    fim += timedelta(days=1)

                # Aguarda 6 horas após o término
                momento_envio = timezone.make_aware(
                    fim + timedelta(hours=6),
                    timezone.get_current_timezone()
                )

                if agora < momento_envio:
                    continue

                self.stdout.write(f"Enviando para: {s.email}")

                link = f"https://siev95.com.br/pesquisa/{s.pesquisa_token}/"

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

                send_mail(
                    "Pesquisa de Satisfação - SiEv",
                    mensagem,
                    settings.DEFAULT_FROM_EMAIL,
                    [s.email],
                    fail_silently=False
                )

                s.pesquisa_enviada = True
                s.data_envio_pesquisa = agora
                s.save(update_fields=[
                    "pesquisa_token",
                    "pesquisa_enviada",
                    "data_envio_pesquisa",
                ])

                enviados += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Pesquisa enviada para {s.email}"
                    )
                )

            except Exception as erro:
                self.stdout.write(
                    self.style.ERROR(str(erro))
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Total de pesquisas enviadas: {enviados}"
            )
        )
