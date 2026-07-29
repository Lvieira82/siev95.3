from datetime import timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
from apps.solicitacoes.models import Solicitacao


class Command(BaseCommand):
    help = "Remove documentos de solicitações com mais de 7 dias"

    def handle(self, *args, **kwargs):

        limite = timezone.localdate() - timedelta(days=7)
        solicitacoes = Solicitacao.objects.filter(
            data_evento__lt=limite
        )
        total = 0

        for s in solicitacoes:

            # Mantém o ofício ao comandante
        
            if s.documento_sanitario:
                s.documento_sanitario.delete(save=False)
                s.documento_sanitario = None
        
            if s.documento_meio_ambiente:
                s.documento_meio_ambiente.delete(save=False)
                s.documento_meio_ambiente = None
        
            if s.oficio_bombeiro:
                s.oficio_bombeiro.delete(save=False)
                s.oficio_bombeiro = None
        
            s.save()

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
