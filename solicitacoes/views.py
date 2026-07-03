from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
import os   
from reportlab.pdfgen import canvas
from .models import Solicitacao
from .forms import SolicitacaoForm
from django.http import HttpResponse
import traceback
from django.shortcuts import render
from django.shortcuts import render
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from pathlib import Path
from django.conf import settings
from datetime import datetime
import uuid
import base64
from io import BytesIO
import qrcode
from django.http import FileResponse, Http404
from django.urls import reverse
   
def minhas_solicitacoes(request):
    return render(
        request,
        'solicitacoes/minhas_solicitacoes.html'
    )

# =====================================================
# HOME
# =====================================================
@login_required
def menu_gestao(request):

    return render(
        request,
        'gestao/menu.html'
    )
def home(request):

    return render(request, 'home.html')


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

                    print(
                        f"ERRO EMAIL: {erro_email}"
                    )

                return render(
                    request,
                    "solicitacoes/sucesso.html",
                    {
                        "protocolo": solicitacao.protocolo
                    }
                )

            except Exception:

                erro = traceback.format_exc()

                return HttpResponse(
                    f"<pre>{erro}</pre>"
                )

        else:

            return HttpResponse(
                f"<pre>{form.errors}</pre>"
            )

    form = SolicitacaoForm()

    return render(
        request,
        "solicitacoes/nova.html",
        {
            "form": form
        }
    )

# =====================================================
# MINHAS SOLICITAÇÕES
# =====================================================

def minhas_solicitacoes(request):

    protocolo = request.GET.get('protocolo')

    solicitacao = None
    erro = None

    if protocolo:

        try:
            solicitacao = Solicitacao.objects.get(
                protocolo=protocolo.upper()
            )

        except Solicitacao.DoesNotExist:
            erro = "Protocolo não encontrado."

    return render(
        request,
        'solicitacoes/minhas.html',
        {
            'solicitacao': solicitacao,
            'erro': erro
        }
    )


# =====================================================
# DASHBOARD OPERACIONAL
# =====================================================

@login_required
def dashboard_operacional(request):

    solicitacoes = Solicitacao.objects.all().order_by('-criado_em')

    total = solicitacoes.count()

    pendentes = solicitacoes.filter(
        status='PENDENTE'
    ).count()

    aprovadas = solicitacoes.filter(
        status='APROVADO'
    ).count()

    return render(
        request,
        'solicitacoes/dashboard.html',
        {
            'solicitacoes': solicitacoes,
            'total': total,
            'pendentes': pendentes,
            'aprovadas': aprovadas,
        }
    )


# =====================================================
# APROVAR SOLICITAÇÃO
# =====================================================

def aprovar_solicitacao(request, id):

    solicitacao = get_object_or_404(
        Solicitacao,
        id=id
    )

    solicitacao.status = 'APROVADO'

    solicitacao.data_assinatura = timezone.now()

    solicitacao.assinado_por = 'Administrador'

    solicitacao.save()
    gerar_pdf_solicitacao(
    solicitacao
    )

    # =================================================
    # EMAIL DE APROVAÇÃO
    # =================================================

    assunto = 'Solicitação Aprovada'

    mensagem = f'''
Olá, {solicitacao.solicitante}!

Sua solicitação foi APROVADA.

PROTOCOLO:
{solicitacao.protocolo}

EVENTO:
{solicitacao.nome_evento}

DATA:
{solicitacao.data_evento}

STATUS:
{solicitacao.status}

PMBA, Uma Força a serviço do cidadão!
    '''

    try:

        send_mail(
            assunto,
            mensagem,
            settings.DEFAULT_FROM_EMAIL,
            [solicitacao.email],
            fail_silently=True
        )

    except Exception as erro:

        print('ERRO AO ENVIAR EMAIL:', erro)

    return redirect('painel_gestao')


# =====================================================
# ALTERAR STATUS
# =====================================================

def alterar_status(request, id, status):

    solicitacao = get_object_or_404(
        Solicitacao,
        id=id
    )

    solicitacao.status = status.upper()

    solicitacao.save()

    return redirect('dashboard_operacional')


# =====================================================
# VERIFICAR AUTENTICIDADE
# =====================================================

def verificar_autenticidade(request, protocolo):

    solicitacao = Solicitacao.objects.filter(
        protocolo=protocolo
    ).first()

    return render(
        request,
        'solicitacoes/verificar.html',
        {
            'solicitacao': solicitacao
        }
    )


# =====================================================
# GERAR PDF
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

def login_gestao(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user:
            login(request, user)
            return redirect('dashboard_operacional')

    return render(
        request,
        'gestao/login.html'
    )


def logout_gestao(request):

    logout(request)

    return redirect('home')

def consultar_protocolo(request):
    return render(
        request,
        'solicitacoes/consultar.html'
    )
    
# =====================================================
# PAINEL DA GESTÃO
# =====================================================

from django.contrib.auth.decorators import login_required

@login_required
def painel_gestao(request):

    return render(
        request,
        'gestao/painel.html'
    )
def home(request):
    return render(request, 'home.html')

@login_required
def documentos_solicitacao(request, id):

    solicitacao = get_object_or_404(
        Solicitacao,
        id=id
    )

    documentos = []

    if solicitacao.documento_sanitario:
        documentos.append({
            "nome": "Documento Sanitário",
            "url": solicitacao.documento_sanitario.url
        })

    if solicitacao.documento_meio_ambiente:
        documentos.append({
            "nome": "Documento Meio Ambiente",
            "url": solicitacao.documento_meio_ambiente.url
        })
    if solicitacao.documento_oficio_comandante:
        documentos.append({
            "nome": "Documento Oficio comandante",
            "url": solicitacao.documento_oficio_comandante.url
        })

    if solicitacao.oficio_bombeiro:
        documentos.append({
            "nome": "Documento Corpo de Bombeiros",
            "url": solicitacao.oficio_bombeiro.url
        })

    return render(
        request,
        "gestao/documentos_solicitacao.html",
        {
            "solicitacao": solicitacao,
            "documentos": documentos,
        }
    )
@login_required
def documentos_solicitacao(request, id):

    solicitacao = get_object_or_404(
        Solicitacao,
        id=id
    )

    documentos = []

    campos = [
        ("sanitario", "Documento Sanitário", solicitacao.documento_sanitario),
        ("meio_ambiente", "Documento Meio Ambiente", solicitacao.documento_meio_ambiente),
        ("Ofício ao Comandante", solicitacao.documento_oficio_comandante),
        ("bombeiro", "Documento Corpo de Bombeiros", solicitacao.oficio_bombeiro),
    ]

    for tipo, nome, arquivo in campos:

        if arquivo:
            documentos.append({
                "nome": nome,
                "url": reverse(
                    "abrir_documento_solicitacao",
                    args=[solicitacao.id, tipo]
                ),
                "arquivo": arquivo.name,
            })

    return render(
        request,
        "gestao/documentos_solicitacao.html",
        {
            "solicitacao": solicitacao,
            "documentos": documentos,
        }
    )

@login_required
def listar_pendentes_opo(request):

    solicitacoes = Solicitacao.objects.filter(
        status="PENDENTE"
    ).order_by("-criado_em")

    return render(
        request,
        "gestao/aprovacoes.html",
        {
            "solicitacoes": solicitacoes,
        }
    )