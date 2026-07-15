import uuid
import os

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


def gerar_protocolo_unico():

    while True:

        protocolo = uuid.uuid4().hex[:8].upper()

        if not Solicitacao.objects.filter(
            protocolo=protocolo
        ).exists():
            return protocolo


def upload_sanitario(instance, filename):

    return f"protocolos/{instance.protocolo}/documento_sanitario.pdf"


def upload_meio_ambiente(instance, filename):

    return f"protocolos/{instance.protocolo}/documento_meio_ambiente.pdf"


def upload_bombeiro(instance, filename):

    return f"protocolos/{instance.protocolo}/documento_bombeiro.pdf"


def upload_comandante(instance, filename):

    return f"protocolos/{instance.protocolo}/oficio_comandante.pdf"


def pasta_opo(instance, filename):

    protocolo = instance.protocolo or "SEM_PROTOCOLO"

    return os.path.join(
        "protocolos",
        protocolo,
        "opo",
        filename
    )


def oficio_comandante(instance, filename):

    return upload_comandante(instance, filename)


class Solicitacao(models.Model):

    STATUS = [
    ("PENDENTE", "Pendente"),
    ("CORRECAO", "Aguardando Correção"),
    ("APROVADO", "Aprovado"),
    ("REJEITADO", "Rejeitado"),
]

    parecer_operacional = models.TextField(
        blank=True,
        null=True
    )

    aprovado_por = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    data_aprovacao = models.DateTimeField(
        blank=True,
        null=True
    )

    protocolo = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
        gerado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opos_geradas",
        verbose_name="OPO gerada por"
    )
    nome_evento = models.CharField(
        max_length=200
    )

    solicitante = models.CharField(
        max_length=200
    )

    cpf = models.CharField(
        max_length=14,
        blank=True,
        null=True
    )

    email = models.EmailField()

    telefone = models.CharField(
        max_length=20
    )

    data_evento = models.DateField()

    hora_inicio = models.TimeField()

    hora_fim = models.TimeField()

    local = models.TextField()

    publico_estimado = models.IntegerField()

    observacoes = models.TextField(
        blank=True
    )

    documento_sanitario = models.FileField(
        upload_to=upload_sanitario,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf"]
            )
        ]
    )

    documento_meio_ambiente = models.FileField(
        upload_to=upload_meio_ambiente,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf"]
            )
        ]
    )

    oficio_bombeiro = models.FileField(
        upload_to=upload_bombeiro,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf"]
            )
        ]
    )

    oficio_comandante = models.FileField(
        upload_to=upload_comandante,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf"]
            )
        ]
    )

    assinado_por = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    data_assinatura = models.DateTimeField(
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="PENDENTE"
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):

        if not self.protocolo:
            self.protocolo = gerar_protocolo_unico()

        super().save(*args, **kwargs)

    def __str__(self):

        return f"{self.protocolo} - {self.nome_evento}"

class MatriculaAutorizada(models.Model):

    matricula = models.CharField(
        max_length=20,
        unique=True
    )

    nome = models.CharField(
        max_length=120
    )

    posto = models.CharField(
        max_length=20,
        blank=True
    )

    unidade = models.CharField(
        max_length=80,
        blank=True
    )

    ativo = models.BooleanField(
        default=True
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Matrícula Autorizada"
        verbose_name_plural = "Matrículas Autorizadas"

    def __str__(self):
        return f"{self.posto} {self.nome} - {self.matricula}"
