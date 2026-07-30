from django.core.management.base import BaseCommand

from apps.solicitacoes.services.pesquisas import enviar_pesquisas_pendentes


class Command(BaseCommand):
    help = "Envia pesquisas de satisfação"

    def handle(self, *args, **kwargs):

        enviados = enviar_pesquisas_pendentes()

        self.stdout.write(
            self.style.SUCCESS(
                f"Total de pesquisas enviadas: {enviados}"
            )
        )
