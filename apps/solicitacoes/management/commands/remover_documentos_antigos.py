from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from apps.solicitacoes.models import Solicitacao


class Command(BaseCommand):
    help = "Remove documentos de solicitações com mais de 7 dias"

    def handle(self, *args, **kwargs):

        limite = timezone.now() - timedelta(days=7)

        solicitacoes = Solicitacao.objects.filter(
            data_criacao__lt=limite
        )

        total = 0

        for s in solicitacoes:

            for campo in [
                "oficio_comandante",
                "documento_sanitario",
                "documento_meio_ambiente",
                "oficio_bombeiro",
            ]:

                arquivo = getattr(s, campo)

                if arquivo:
                    arquivo.delete(save=False)
                    setattr(s, campo, None)

            s.save()
            total += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{total} solicitações processadas."
            )
        )
