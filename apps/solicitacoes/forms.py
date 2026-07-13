from django import forms
from django.core.exceptions import ValidationError
from datetime import date, timedelta
import re
from .models import Solicitacao
from django import forms
from django.core.exceptions import ValidationError
from datetime import date, timedelta
import re
from .models import Solicitacao
from .utils import analisar_datas_oficio


# ==========================================================
# VALIDAÇÃO DE ARQUIVO PDF
# ==========================================================

def validar_pdf(arquivo):

    if not arquivo:
        return

    extensao = arquivo.name.split(".")[-1].lower()

    if extensao != "pdf":
        raise ValidationError(
            "Somente arquivos PDF são permitidos."
        )


# ==========================================================
# FORMULÁRIO DE SOLICITAÇÃO EXTERNA
# ==========================================================

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


    # ======================================================
    # INICIALIZAÇÃO DO FORMULÁRIO
    # ======================================================

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Inicializa os atributos usados pela análise do ofício.
        # Isso evita AttributeError posteriormente na view.

        self.aviso_multiplas_datas = False
        self.datas_encontradas_oficio = []

        data_minima = date.today() + timedelta(days=3)

        self.fields["data_evento"].widget.attrs.update({
            "type": "date",
            "min": data_minima.strftime("%Y-%m-%d"),
        })


    # ======================================================
    # VALIDAÇÃO DO TELEFONE
    # ======================================================

    def clean_telefone(self):

        telefone = self.cleaned_data.get("telefone")

        padrao = r"^\(\d{2}\)\s\d{5}-\d{4}$"

        if not telefone or not re.match(padrao, telefone):

            raise forms.ValidationError(
                "Telefone inválido. Use (99) 99999-9999"
            )

        return telefone


    # ======================================================
    # VALIDAÇÃO DA DATA DO EVENTO
    # ======================================================

    def clean_data_evento(self):

        data_evento = self.cleaned_data.get("data_evento")

        data_minima = date.today() + timedelta(days=3)

        if data_evento and data_evento < data_minima:

            raise forms.ValidationError(
                "A data do evento deve ser, no mínimo, "
                "3 dias após a data da informação."
            )

        return data_evento


    # ======================================================
    # VALIDAÇÃO DO DOCUMENTO SANITÁRIO
    # ======================================================

    def clean_documento_sanitario(self):

        arquivo = self.cleaned_data.get(
            "documento_sanitario"
        )

        if arquivo:
            validar_pdf(arquivo)

        return arquivo


    # ======================================================
    # VALIDAÇÃO DO DOCUMENTO DE MEIO AMBIENTE
    # ======================================================

    def clean_documento_meio_ambiente(self):

        arquivo = self.cleaned_data.get(
            "documento_meio_ambiente"
        )

        if arquivo:
            validar_pdf(arquivo)

        return arquivo


    # ======================================================
    # VALIDAÇÃO DO OFÍCIO AO COMANDANTE
    # ======================================================

    def clean_oficio_comandante(self):

        arquivo = self.cleaned_data.get(
            "oficio_comandante"
        )

        if arquivo:
            validar_pdf(arquivo)

        return arquivo


    # ======================================================
    # VALIDAÇÃO DO DOCUMENTO DO CORPO DE BOMBEIROS
    # ======================================================

    def clean_oficio_bombeiro(self):

        arquivo = self.cleaned_data.get(
            "oficio_bombeiro"
        )

        if arquivo:
            validar_pdf(arquivo)

        return arquivo


    # ======================================================
    # VALIDAÇÃO GERAL DO FORMULÁRIO
    # ======================================================

    def clean(self):

        cleaned_data = super().clean()

        publico = cleaned_data.get(
            "publico_estimado"
        )

        documento_sanitario = cleaned_data.get(
            "documento_sanitario"
        )

        documento_meio_ambiente = cleaned_data.get(
            "documento_meio_ambiente"
        )

        oficio_comandante = cleaned_data.get(
            "oficio_comandante"
        )

        bombeiro = cleaned_data.get(
            "oficio_bombeiro"
        )

        data_evento = cleaned_data.get(
            "data_evento"
        )


        # ==================================================
        # DOCUMENTOS OBRIGATÓRIOS
        # ==================================================

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
                "Quando houver estrutura de palco ou evento "
                "em local confinado, o Documento do Corpo "
                "de Bombeiros é obrigatório."
            )


        # ==================================================
        # ANÁLISE AUTOMÁTICA DA DATA DO OFÍCIO
        # ==================================================

        if oficio_comandante and data_evento:

            try:

                resultado = analisar_datas_oficio(
                    oficio_comandante,
                    data_evento
                )

            except Exception as erro:

                # Mostra o erro real nos logs do Render,
                # mas não expõe detalhes técnicos ao usuário.

                print(
                    "ERRO AO ANALISAR OFÍCIO:",
                    repr(erro)
                )

                raise forms.ValidationError(
                    "Não foi possível analisar o Ofício ao "
                    "Comandante. Verifique se o arquivo é um "
                    "PDF válido e legível e tente novamente."
                )


            # ==============================================
            # NENHUMA DATA FOI ENCONTRADA
            # ==============================================

            if not resultado["datas"]:

                raise forms.ValidationError(
                    "Não foi possível identificar uma data no "
                    "Ofício ao Comandante. Confira se o documento "
                    "está legível e se contém a data do evento."
                )


            # ==============================================
            # ENCONTROU DATA, MAS NENHUMA COINCIDE
            # ==============================================

            if not resultado["valido"]:

                datas_lidas = ", ".join(
                    item["data"].strftime("%d/%m/%Y")
                    for item in resultado["datas"]
                )

                raise forms.ValidationError(
                    "A data do ofício está diferente da data "
                    "informada. Confira as informações. "
                    f"Data(s) identificada(s) no documento: "
                    f"{datas_lidas}."
                )


            # ==============================================
            # DATA CORRETA E MÚLTIPLAS DATAS ENCONTRADAS
            # ==============================================

            self.aviso_multiplas_datas = (
                resultado["multiplas_datas"]
            )

            self.datas_encontradas_oficio = (
                resultado["datas"]
            )


        return cleaned_data


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

        # Remove a restrição visual de data mínima no HTML
        if "data_evento" in self.fields:
            self.fields["data_evento"].widget.attrs.pop("min", None)

    def clean_data_evento(self):
        """
        No lançamento manual, aceita qualquer data:
        passada, atual ou futura.
        """
        return self.cleaned_data.get("data_evento")

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
