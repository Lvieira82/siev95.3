from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.solicitacoes.models import Solicitacao


class Command(BaseCommand):
    help = (
        "Remove os documentos temporários de solicitações "
        "cujos eventos ocorreram há mais de 7 dias."
    )

    def handle(self, *args, **kwargs):

        limite = timezone.localdate() - timedelta(days=7)
    
        solicitacoes = Solicitacao.objects.filter(
            data_evento__lt=limite,
            documentos_expurgados=False
        )
            
        total = 0
    
        for s in solicitacoes:
    
            alterou = False
    
            self.stdout.write(
                f"Processando protocolo {s.protocolo}..."
            )
    
            if s.documento_sanitario:
                s.documento_sanitario.delete(save=False)
                s.documento_sanitario = None
                alterou = True
                self.stdout.write("  ✔ Documento Sanitário removido")
    
            if s.documento_meio_ambiente:
                s.documento_meio_ambiente.delete(save=False)
                s.documento_meio_ambiente = None
                alterou = True
                self.stdout.write("  ✔ Documento Meio Ambiente removido")
    
            if s.oficio_bombeiro:
                s.oficio_bombeiro.delete(save=False)
                s.oficio_bombeiro = None
                alterou = True
                self.stdout.write("  ✔ Documento Bombeiro removido")
    
            # Mantém o oficio_comandante
    
            if alterou:
                s.save()
                total += 1
    
        self.stdout.write(
            self.style.SUCCESS(
                f"\nConcluído! {total} solicitações tiveram os documentos temporários removidos."
            )
        )
