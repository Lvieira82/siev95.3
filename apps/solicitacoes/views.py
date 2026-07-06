import os
import base64
from io import BytesIO
from datetime import date, timedelta

import qrcode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.http import FileResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from .models import Solicitacao
from .forms import SolicitacaoForm, SolicitacaoManualForm


# =====================================================
# HOME
# =====================================================

def home(request):
    return render(request, "home.html")


# =====================================================
# NOVA SOLICITAÇÃO
# =====================================================

def nova_solicitacao(request):

    if request.method == "POST":

        form = SolicitacaoForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            try:
                solicitacao = form.save(commit=False)
                solicitacao.status = "PENDENTE"
                solicitacao.save()

                assunto = "Solicitação de Evento Recebida"

                mensagem = f"""
Olá, {solicitacao.solicitante}!

Sua solicitação foi recebida com sucesso.

PROTOCOLO:
{solicitacao.protocolo}

EVENTO:
{solicitacao.nome_evento}

DATA:
{solicitacao.data_evento}

STATUS:
{solicitacao.status}

Guarde este protocolo para futuras consultas.

PMBA - Uma força a serviço do cidadão.
"""

                try:
                    send_mail(
                        assunto,
                        mensagem,
                        settings.DEFAULT_FROM_EMAIL,
                        [solicitacao.email],
                        fail_silently=False
                    )

                except Exception as erro_email:
                    print("ERRO AO ENVIAR EMAIL:")
                    print(erro_email)

                return render(
                    request,
                    "solicitacoes/sucesso.html",
                    {
                        "protocolo": solicitacao.protocolo
                    }
                )

            except Exception as erro:
                form.add_error(
                    None,
                    f"Ocorreu um erro ao salvar a solicitação: {erro}"
                )

    else:
        form = SolicitacaoForm()

    return render(
        request,
        "solicitacoes/nova.html",
        {
            "form": form
        }
    )


# =====================================================
# CONSULTAR PROTOCOLO
# =====================================================

def consultar_protocolo(request):

    protocolo = request.GET.get("protocolo")

    solicitacao = None
    erro = None

    if protocolo:

        solicitacao = Solicitacao.objects.filter(
            protocolo=protocolo.upper()
        ).first()

        if not solicitacao:
            erro = "Protocolo não encontrado."

    return render(
        request,
        "solicitacoes/consultar.html",
        {
            "solicitacao": solicitacao,
            "erro": erro,
        }
    )


# =====================================================
# MINHAS SOLICITAÇÕES
# =====================================================

def minhas_solicitacoes(request):

    protocolo = request.GET.get("protocolo")

    solicitacao = None
    erro = None

    if protocolo:

        solicitacao = Solicitacao.objects.filter(
            protocolo=protocolo.upper()
        ).first()

        if not solicitacao:
            erro = "Protocolo não encontrado."

    return render(
        request,
        "solicitacoes/minhas.html",
        {
            "solicitacao": solicitacao,
            "erro": erro,
        }
    )


# =====================================================
# LOGIN / LOGOUT GESTÃO
# =====================================================

def login_gestao(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect("painel_gestao")

        return render(
            request,
            "gestao/login.html",
            {
                "erro": "Usuário ou senha inválidos."
            }
        )

    return render(
        request,
        "gestao/login.html"
    )


def logout_gestao(request):

    logout(request)

    return redirect("home")


# =====================================================
# PAINEL DA GESTÃO
# =====================================================

@login_required
def painel_gestao(request):

    hoje = date.today()

    pendentes_opo = Solicitacao.objects.filter(status="PENDENTE").count()

    eventos_semana = Solicitacao.objects.filter(
        data_evento__gte=hoje,
        data_evento__lte=hoje + timedelta(days=7)
    ).count()

    eventos_mes = Solicitacao.objects.filter(
        data_evento__year=hoje.year,
        data_evento__month=hoje.month
    ).count()

    proximos_eventos = Solicitacao.objects.filter(
        data_evento__gte=hoje
    ).order_by("data_evento", "hora_inicio")[:10]

    usuarios = User.objects.count()

    return render(request, "gestao/painel_gestao.html", {
        "pendentes_opo": pendentes_opo,
        "eventos_semana": eventos_semana,
        "eventos_mes": eventos_mes,
        "proximos_eventos": proximos_eventos,
        "usuarios": usuarios,
    })

# =====================================================
# DASHBOARD OPERACIONAL
# =====================================================

@login_required
def dashboard_operacional(request):

    solicitacoes = Solicitacao.objects.all().order_by(
        "-criado_em"
    )

    total = solicitacoes.count()

    pendentes = solicitacoes.filter(
        status="PENDENTE"
    ).count()

    aprovadas = solicitacoes.filter(
        status="APROVADO"
    ).count()

    return render(
        request,
        "solicitacoes/dashboard.html",
        {
            "solicitacoes": solicitacoes,
            "total": total,
            "pendentes": pendentes,
            "aprovadas": aprovadas,
        }
    )


# =====================================================
# AGENDA
# =====================================================

@login_required
def agenda_gestao(request):

    hoje = date.today()

    eventos = Solicitacao.objects.filter(
        data_evento__gte=hoje
    ).order_by(
        "data_evento",
        "hora_inicio"
    )

    return render(
        request,
        "gestao/agenda.html",
        {
            "eventos": eventos
        }
    )


# =====================================================
# LANÇAMENTO MANUAL
# =====================================================

@login_required
def lancamento_manual(request):

    if request.method == "POST":

        form = SolicitacaoManualForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            solicitacao = form.save(commit=False)
            solicitacao.status = "PENDENTE"
            solicitacao.usuario = request.user

            if not solicitacao.publico_estimado:
                solicitacao.publico_estimado = 0

            solicitacao.save()

            messages.success(
                request,
                f"Lançamento manual salvo. Protocolo: {solicitacao.protocolo}"
            )

            return redirect("listar_pendentes_opo")

        else:
            print("ERROS DO FORMULÁRIO MANUAL:")
            print(form.errors)

    else:
        form = SolicitacaoManualForm()

    return render(
        request,
        "gestao/lancamento_manual.html",
        {
            "form": form
        }
    )
# =====================================================
# APROVAÇÕES / PENDENTES DE OPO
# =====================================================

@login_required
def listar_pendentes_opo(request):

    solicitacoes = Solicitacao.objects.filter(
        status="PENDENTE"
    ).order_by(
        "data_evento",
        "hora_inicio"
    )

    return render(
        request,
        "gestao/aprovacoes.html",
        {
            "solicitacoes": solicitacoes,
        }
    )


@login_required
def aprovar_solicitacao(request, id):

    solicitacao = get_object_or_404(
        Solicitacao,
        id=id
    )

    solicitacao.status = "APROVADO"
    solicitacao.aprovado_por = request.user.username
    solicitacao.data_aprovacao = timezone.now()
    solicitacao.data_assinatura = timezone.now()
    solicitacao.assinado_por = request.user.username
    solicitacao.save()

    assunto = "Ordem de Policiamento Criada"

    mensagem = f"""
Olá, {solicitacao.solicitante}!

Sua solicitação foi aprovada e a Ordem de Policiamento foi criada.

PROTOCOLO:
{solicitacao.protocolo}

EVENTO:
{solicitacao.nome_evento}

DATA:
{solicitacao.data_evento}

STATUS:
Ordem de Policiamento Criada

PMBA - Uma força a serviço do cidadão.
"""

    try:
        send_mail(
            assunto,
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [solicitacao.email],
            fail_silently=True
        )

    except Exception as erro:
        print("ERRO AO ENVIAR EMAIL DE APROVAÇÃO:", erro)

    return redirect(
        "gerar_opo",
        id=solicitacao.id
    )


# =====================================================
# GERAR OPO
# =====================================================

@login_required
def gerar_opo(request, id):

    solicitacao = get_object_or_404(
        Solicitacao,
        id=id,
        status="APROVADO"
    )

    data_geracao = timezone.localtime()

    url_verificacao = request.build_absolute_uri(
        f"/verificar/{solicitacao.protocolo}/"
    )

    qr_img = qrcode.make(url_verificacao)

    buffer = BytesIO()

    qr_img.save(
        buffer,
        format="PNG"
    )

    qr_base64 = base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")

    qr_base64 = f"data:image/png;base64,{qr_base64}"

    return render(
        request,
        "solicitacoes/opo_pdf.html",
        {
            "solicitacao": solicitacao,
            "data_geracao": data_geracao,
            "qr_base64": qr_base64,
            "url_verificacao": url_verificacao,
        }
    )


# =====================================================
# DOCUMENTOS ANEXOS
# =====================================================

@login_required
def documentos_solicitacao(request, id):

    solicitacao = get_object_or_404(
        Solicitacao,
        id=id
    )

    documentos = [
        {
            "nome": "Documento Sanitário",
            "url": reverse(
                "abrir_documento_solicitacao",
                args=[solicitacao.id, "sanitario"]
            ),
            "arquivo": solicitacao.documento_sanitario,
        },
        {
            "nome": "Documento Meio Ambiente",
            "url": reverse(
                "abrir_documento_solicitacao",
                args=[solicitacao.id, "meio_ambiente"]
            ),
            "arquivo": solicitacao.documento_meio_ambiente,
        },
        {
            "nome": "Ofício ao Comandante",
            "url": reverse(
                "abrir_documento_solicitacao",
                args=[solicitacao.id, "comandante"]
            ),
            "arquivo": solicitacao.oficio_comandante,
        },
        {
            "nome": "Documento Corpo de Bombeiros",
            "url": reverse(
                "abrir_documento_solicitacao",
                args=[solicitacao.id, "bombeiro"]
            ),
            "arquivo": solicitacao.oficio_bombeiro,
        },
    ]

    return render(
        request,
        "gestao/documentos_solicitacao.html",
        {
            "solicitacao": solicitacao,
            "documentos": documentos,
        }
    )


@login_required
def abrir_documento_solicitacao(request, id, tipo):

    solicitacao = get_object_or_404(
        Solicitacao,
        id=id
    )

    arquivos = {
        "sanitario": solicitacao.documento_sanitario,
        "meio_ambiente": solicitacao.documento_meio_ambiente,
        "comandante": solicitacao.oficio_comandante,
        "bombeiro": solicitacao.oficio_bombeiro,
    }

    arquivo = arquivos.get(tipo)

    if not arquivo or not arquivo.name:
        raise Http404("Documento não informado.")

    if not os.path.exists(arquivo.path):
        raise Http404("Arquivo não encontrado no disco.")

    return FileResponse(
        open(arquivo.path, "rb"),
        content_type="application/pdf"
    )


# =====================================================
# BAIXAR PROCESSO EM ZIP
# =====================================================

@login_required
def baixar_processo(request, id):

    import zipfile

    solicitacao = get_object_or_404(
        Solicitacao,
        id=id
    )

    buffer = BytesIO()

    arquivos = [
        solicitacao.documento_sanitario,
        solicitacao.documento_meio_ambiente,
        solicitacao.oficio_comandante,
        solicitacao.oficio_bombeiro,
    ]

    with zipfile.ZipFile(buffer, "w") as zip_file:

        for arquivo in arquivos:

            if arquivo and arquivo.name and os.path.exists(arquivo.path):

                zip_file.write(
                    arquivo.path,
                    os.path.basename(arquivo.path)
                )

    buffer.seek(0)

    nome_zip = f"processo_{solicitacao.protocolo}.zip"

    response = FileResponse(
        buffer,
        as_attachment=True,
        filename=nome_zip
    )

    return response


# =====================================================
# ALTERAR STATUS
# =====================================================

@login_required
def alterar_status(request, id, status):

    solicitacao = get_object_or_404(
        Solicitacao,
        id=id
    )

    solicitacao.status = status.upper()
    solicitacao.save()

    return redirect("dashboard_operacional")


# =====================================================
# VERIFICAR AUTENTICIDADE
# =====================================================

def verificar_autenticidade(request, protocolo):

    solicitacao = Solicitacao.objects.filter(
        protocolo=protocolo.upper()
    ).first()

    return render(
        request,
        "solicitacoes/verificar.html",
        {
            "solicitacao": solicitacao
        }
    )
#=====================================================
# DESTINOS DA OPO
# =====================================================   
@login_required
def opos_geradas(request):

    solicitacoes = Solicitacao.objects.filter(
        status="APROVADO"
    ).order_by("-data_aprovacao", "-criado_em")

    return render(
        request,
        "gestao/opos_geradas.html",
        {
            "solicitacoes": solicitacoes
        }
    )


@login_required
def detalhe_opo(request, id):

    solicitacao = get_object_or_404(
        Solicitacao,
        id=id,
        status="APROVADO"
    )

    return render(
        request,
        "gestao/detalhe_opo.html",
        {
            "solicitacao": solicitacao
        }
    )
