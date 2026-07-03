from django import forms
from django.core.exceptions import ValidationError
from datetime import date, timedelta
import re

from .models import Solicitacao


def validar_pdf(arquivo):

    if not arquivo:
        return

    extensao = arquivo.name.split(".")[-1].lower()

    if extensao != "pdf":
        raise ValidationError(
            "Somente arquivos PDF são permitidos."
        )


class SolicitacaoForm(forms.ModelForm):

    class Meta:

        model = Solicitacao

        exclude = [
            "status",
            "parecer_operacional",
            "aprovado_por",
            "data_aprovacao",
            "protocolo",
            "usuario",
            "assinado_por",
            "data_assinatura",
            "criado_em",
            "opo_pdf",
        ]

        widgets = {

            "cpf": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "000.000.000-00",
                "maxlength": "14",
            }),

            "telefone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "(99) 99999-9999",
                "maxlength": "15",
            }),

            "data_evento": forms.DateInput(attrs={
                "type": "date",
            }),

            "hora_inicio": forms.TimeInput(attrs={
                "type": "time",
            }),

            "hora_fim": forms.TimeInput(attrs={
                "type": "time",
            }),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        data_minima = date.today() + timedelta(days=3)

        self.fields["data_evento"].widget.attrs.update({
            "type": "date",
            "min": data_minima.strftime("%Y-%m-%d"),
        })

    def clean_telefone(self):

        telefone = self.cleaned_data.get("telefone")

        padrao = r"^\(\d{2}\)\s\d{5}-\d{4}$"

        if not telefone or not re.match(padrao, telefone):

            raise forms.ValidationError(
                "Telefone inválido. Use (99) 99999-9999"
            )

        return telefone

    def clean_data_evento(self):

        data_evento = self.cleaned_data.get("data_evento")

        data_minima = date.today() + timedelta(days=3)

        if data_evento and data_evento < data_minima:

            raise forms.ValidationError(
                "A data do evento deve ser, no mínimo, 3 dias após a data da informação."
            )

        return data_evento

    def clean(self):

        cleaned_data = super().clean()

        publico = cleaned_data.get("publico_estimado")

        documento_sanitario = cleaned_data.get("documento_sanitario")

        documento_meio_ambiente = cleaned_data.get("documento_meio_ambiente")

        oficio_comandante = cleaned_data.get("oficio_comandante")

        bombeiro = cleaned_data.get("oficio_bombeiro")

        if not documento_sanitario:

            raise forms.ValidationError(
                "O Documento Sanitário é obrigatório."
            )

        if not documento_meio_ambiente:

            raise forms.ValidationError(
                "O Documento de Meio Ambiente é obrigatório."
            )

        if not oficio_comandante:

            raise forms.ValidationError(
                "O Ofício ao Comandante da Unidade é obrigatório."
            )

        if publico == 1 and not bombeiro:

            raise forms.ValidationError(
                "Quando houver estrutura de palco ou evento em local confinado, o Documento do Corpo de Bombeiros é obrigatório."
            )

        return cleaned_data

    def clean_documento_sanitario(self):

        arquivo = self.cleaned_data.get("documento_sanitario")

        if arquivo:
            validar_pdf(arquivo)

        return arquivo

    def clean_documento_meio_ambiente(self):

        arquivo = self.cleaned_data.get("documento_meio_ambiente")

        if arquivo:
            validar_pdf(arquivo)

        return arquivo

    def clean_oficio_comandante(self):

        arquivo = self.cleaned_data.get("oficio_comandante")

        if arquivo:
            validar_pdf(arquivo)

        return arquivo

    def clean_oficio_bombeiro(self):

        arquivo = self.cleaned_data.get("oficio_bombeiro")

        if arquivo:
            validar_pdf(arquivo)

        return arquivo
class SolicitacaoManualForm(SolicitacaoForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        campos_nao_obrigatorios = [
            "publico_estimado",
            "documento_sanitario",
            "documento_meio_ambiente",
            "oficio_comandante",
            "oficio_bombeiro",
        ]

        for campo in campos_nao_obrigatorios:
            if campo in self.fields:
                self.fields[campo].required = False

        if "cpf" in self.fields:
            self.fields["cpf"].widget.attrs.update({
                "placeholder": "Somente números",
                "maxlength": "11",
            })

        if "telefone" in self.fields:
            self.fields["telefone"].widget.attrs.update({
                "placeholder": "Somente números",
                "maxlength": "11",
            })

        if "data_evento" in self.fields:
            self.fields["data_evento"].widget.attrs.pop("min", None)

    def clean_telefone(self):
        telefone = self.cleaned_data.get("telefone", "")
        telefone = "".join(filter(str.isdigit, telefone))

        if len(telefone) not in (10, 11):
            raise forms.ValidationError(
                "Informe apenas os números do telefone."
            )

        return telefone

    def clean_cpf(self):
        cpf = self.cleaned_data.get("cpf", "")
        cpf = "".join(filter(str.isdigit, cpf))

        if cpf and len(cpf) != 11:
            raise forms.ValidationError(
                "Informe apenas os 11 números do CPF."
            )

        return cpf

    def clean(self):
        cleaned_data = super(SolicitacaoForm, self).clean()

        if not cleaned_data.get("publico_estimado"):
            cleaned_data["publico_estimado"] = 0

        return cleaned_data