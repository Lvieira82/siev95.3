from .models import Solicitacao
from .forms import SolicitacaoForm, SolicitacaoManualForm
from django.shortcuts import render, get_object_or_404, redirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
import os
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone
from .models import Solicitacao
from django.utils import timezone
from django.conf import settings
import tempfile
from reportlab.pdfgen import canvas
from .models import Solicitacao
from .forms import SolicitacaoForm
import traceback
import os
import zipfile
import os
from django.urls import reverse
import qrcode
from django.shortcuts import render
import base64
from io import BytesIO
import qrcode
from django.http import HttpResponse, FileResponse, Http404
from .models import Solicitacao
from django.http import (
    HttpResponse,
    FileResponse
)
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

from django.contrib.auth import (
    authenticate,
    login,
    logout
)


@login_required
def aprovar_solicitacao(request, id):

    solicitacao = get_object_or_404(
        Solicitacao,
        id=id
    )

    solicitacao.status = "APROVADO"
    solicitacao.data_aprovacao = timezone.now()
    solicitacao.aprovado_por = request.user.get_full_name() or request.user.username

    if not solicitacao.numero_opo:
        solicitacao.numero_opo = solicitacao.protocolo
    solicitacao.save()

    return redirect(
        "gerar_opo",
        id=solicitacao.id
    )





def link_callback(uri, rel):

    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(
            settings.MEDIA_ROOT,
            uri.replace(settings.MEDIA_URL, "")
        )

    elif uri.startswith(settings.STATIC_URL):
        path = os.path.join(
            settings.STATIC_ROOT,
            uri.replace(settings.STATIC_URL, "")
        )

    else:
        path = uri

    if not os.path.isfile(path):
        raise Exception(
            f"Arquivo não encontrado para PDF: {path}"
        )

    return path


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

    # QR CODE EM MEMÓRIA
    qr = qrcode.make(url_verificacao)

    buffer = BytesIO()

    qr.save(
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
# CONSULTA DE PROTOCOLO
# =====================================================

def consultar_protocolo(request):

    protocolo = request.GET.get("protocolo")

    solicitacao = None
    erro = None

    if protocolo:

        solicitacao = (
            Solicitacao.objects
            .filter(
                protocolo=protocolo.upper()
            )
            .first()
        )

        if not solicitacao:
            erro = "Protocolo não encontrado."

    return render(
        request,
        'solicitacoes/consultar.html',
        {
            'solicitacao': solicitacao,
            'erro': erro
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

        try:

            solicitacao = Solicitacao.objects.get(
                protocolo=protocolo.upper()
            )

        except Solicitacao.DoesNotExist:

            erro = "Protocolo não encontrado."

    return render(
        request,
        "solicitacoes/minhas.html",
        {
            "solicitacao": solicitacao,
            "erro": erro
        }
    )


# =====================================================
# LOGIN GESTÃO
# =====================================================



def login_gestao(request):

    erro = None

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user:

            login(request, user)

            return redirect("painel_gestao")

        erro = "Usuário ou senha inválidos."

    return render(
        request,
        "gestao/login.html",
        {
            "erro": erro
        }
    )

# =====================================================
# LOGOUT
# =====================================================

def logout_gestao(request):

    logout(request)

    return redirect("home")


# =====================================================
# MENU GESTÃO
# =====================================================

@login_required
def menu_gestao(request):

    return render(
        request,
        "gestao/menu.html"
    )


# =====================================================
# PAINEL GESTÃO
# =====================================================

@login_required
def painel_gestao(request):

    pendentes_opo = Solicitacao.objects.filter(
        status="PENDENTE"
    ).count()

    return render(
        request,
        "gestao/painel_gestao.html",
        {
            "pendentes_opo": pendentes_opo,
        }
    )

# =====================================================
# DASHBOARD
# =====================================================

@login_required
def dashboard_operacional(request):

    solicitacoes = (
        Solicitacao.objects
        .all()
        .order_by("-criado_em")
    )

    total = solicitacoes.count()

    pendentes = (
        solicitacoes
        .filter(status="PENDENTE")
        .count()
    )

    aprovadas = (
        solicitacoes
        .filter(status="APROVADO")
        .count()
    )

    rejeitadas = (
        solicitacoes
        .filter(status="REJEITADO")
        .count()
    )

    return render(
        request,
        "solicitacoes/dashboard.html",
        {
            "solicitacoes": solicitacoes,
            "total": total,
            "pendentes": pendentes,
            "aprovadas": aprovadas,
            "rejeitadas": rejeitadas,
        }
    )


# =====================================================
# APROVAR SOLICITAÇÃO
# =====================================================
@login_required
def aprovacoes(request):

    solicitacoes = (
        Solicitacao.objects
        .filter(status="PENDENTE")
        .order_by("-criado_em")
    )

    return render(
        request,
        "gestao/aprovacoes.html",
        {
            "solicitacoes": solicitacoes
        }
    )


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

    return redirect(
        "dashboard_operacional"
    )


# =====================================================
# VERIFICAÇÃO DE AUTENTICIDADE
# =====================================================

def verificar_autenticidade(
    request,
    protocolo
):

    solicitacao = (
        Solicitacao.objects
        .filter(
            protocolo=protocolo
        )
        .first()
    )

    return render(
        request,
        "solicitacoes/verificar.html",
        {
            "solicitacao": solicitacao
        }
    )

def gerar_pdf_arquivo(solicitacao):

    pasta = os.path.join(
        settings.MEDIA_ROOT,
        "protocolos",
        solicitacao.protocolo
    )

    os.makedirs(
        pasta,
        exist_ok=True
    )

    caminho_pdf = os.path.join(
        pasta,
        f"formulario_{solicitacao.protocolo}.pdf"
    )

    pdf = canvas.Canvas(caminho_pdf)

    y = 800

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(160, y, "FORMULÁRIO DE SOLICITAÇÃO DE EVENTO")

    y -= 50
    pdf.setFont("Helvetica", 11)

    dados = [
        f"Protocolo: {solicitacao.protocolo}",
        f"Solicitante: {solicitacao.solicitante}",
        f"CPF: {solicitacao.cpf}",
        f"E-mail: {solicitacao.email}",
        f"Telefone: {solicitacao.telefone}",
        f"Evento: {solicitacao.nome_evento}",
        f"Local: {solicitacao.local}",
        f"Data: {solicitacao.data_evento}",
        f"Início: {solicitacao.hora_inicio}",
        f"Fim: {solicitacao.hora_fim}",
        f"Público estimado: {solicitacao.publico_estimado}",
        f"Status: {solicitacao.status}",
        f"Criado em: {solicitacao.criado_em}",
    ]

    for linha in dados:
        pdf.drawString(50, y, linha)
        y -= 25

    y -= 15
    pdf.drawString(50, y, "Observações:")
    y -= 25
    pdf.drawString(50, y, str(solicitacao.observacoes or ""))

    pdf.showPage()
    pdf.save()

    return caminho_pdf
# =====================================================
# GERAR PDF
# =====================================================

@login_required
def gerar_pdf(request, id):

    solicitacao = get_object_or_404(
        Solicitacao,
        id=id
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response[
        "Content-Disposition"
    ] = (
        f'inline; filename="solicitacao_{id}.pdf"'
    )

    pdf = canvas.Canvas(response)

    y = 800

    pdf.setFont(
        "Helvetica-Bold",
        16
    )

    pdf.drawString(
        180,
        y,
        "SOLICITAÇÃO DE EVENTO"
    )

    y -= 50

    pdf.setFont(
        "Helvetica",
        11
    )

    dados = [

        f"Protocolo: {solicitacao.protocolo}",
        f"Solicitante: {solicitacao.solicitante}",
        f"CPF: {solicitacao.cpf}",
        f"E-mail: {solicitacao.email}",
        f"Telefone: {solicitacao.telefone}",
        f"Evento: {solicitacao.nome_evento}",
        f"Local: {solicitacao.local}",
        f"Data: {solicitacao.data_evento}",
        f"Início: {solicitacao.hora_inicio}",
        f"Fim: {solicitacao.hora_fim}",
        f"Público Estimado: {solicitacao.publico_estimado}",
        f"Status: {solicitacao.status}",
        f"Criado em: {solicitacao.criado_em}",

    ]

    for linha in dados:

        pdf.drawString(
            50,
            y,
            linha
        )

        y -= 25

    y -= 15

    pdf.drawString(
        50,
        y,
        "Observações:"
    )

    y -= 25

    pdf.drawString(
        50,
        y,
        str(
            solicitacao.observacoes
        )
    )

    pdf.showPage()

    pdf.save()

    return response

# =====================================================
# BAIXAR PROCESSO
# =====================================================
@login_required
def baixar_processo(request, id):

    solicitacao = get_object_or_404(Solicitacao, id=id)

    protocolo = solicitacao.protocolo

    pasta_processo = os.path.join(
        settings.MEDIA_ROOT,
        "protocolos",
        protocolo
    )

    os.makedirs(pasta_processo, exist_ok=True)

    pdf_path = gerar_pdf_arquivo(solicitacao)

    zip_path = os.path.join(
        pasta_processo,
        f"processo_{protocolo}.zip"
    )

    with zipfile.ZipFile(
        zip_path,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zipf:

        zipf.write(
            pdf_path,
            f"{protocolo}/formulario_{protocolo}.pdf"
        )

        arquivos = [
            solicitacao.documento_sanitario,
            solicitacao.documento_meio_ambiente,
            solicitacao.oficio_bombeiro,
        ]

        for arquivo in arquivos:

            if arquivo and os.path.exists(arquivo.path):

                zipf.write(
                    arquivo.path,
                    f"{protocolo}/{os.path.basename(arquivo.path)}"
                )

    return FileResponse(
        open(zip_path, "rb"),
        as_attachment=True,
        filename=f"processo_{protocolo}.zip"
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
def nova_solicitacao(request):

    if request.method == "POST":

        form = SolicitacaoForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            solicitacao = form.save(commit=False)
            solicitacao.status = "PENDENTE"
            solicitacao.save()

            gerar_pdf_arquivo(solicitacao)

            assunto = "Solicitação Recebida - SiEv"

            mensagem = f"""
Olá, {solicitacao.solicitante}!

Sua informação foi recebida com sucesso.

PROTOCOLO:
{solicitacao.protocolo}

EVENTO:
{solicitacao.nome_evento}

DATA:
{solicitacao.data_evento}

STATUS:
{solicitacao.status}

Guarde este protocolo para acompanhamento.

PMBA - Uma Força a Serviço do Cidadão.
"""

            try:
                send_mail(
                    assunto,
                    mensagem,
                    settings.DEFAULT_FROM_EMAIL,
                    [solicitacao.email],
                    fail_silently=False
                )

                print("EMAIL ENVIADO COM SUCESSO")

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

    else:
        form = SolicitacaoForm()

    return render(
        request,
        "solicitacoes/nova.html",
        {
            "form": form
        }
    )
def home(request):
    return render(request, "home.html")
@login_required
def abrir_documento_solicitacao(request, id, tipo):

    solicitacao = get_object_or_404(Solicitacao, id=id)

    arquivos = {
        "sanitario": solicitacao.documento_sanitario,
        "meio_ambiente": solicitacao.documento_meio_ambiente,
        "bombeiro": solicitacao.oficio_bombeiro,
    }

    arquivo = arquivos.get(tipo)

    if not arquivo or not arquivo.name:
        raise Http404("Documento não encontrado.")

    if not os.path.exists(arquivo.path):
        raise Http404("Arquivo não existe no disco.")

    return FileResponse(
        open(arquivo.path, "rb"),
        content_type="application/pdf"
    )


@login_required
def visualizar_documentos(request, id):

    solicitacao = get_object_or_404(Solicitacao, id=id)

    documentos = []

    campos = [
        ("sanitario", "Documento Sanitário", solicitacao.documento_sanitario),
        ("meio_ambiente", "Documento Meio Ambiente", solicitacao.documento_meio_ambiente),
        ("bombeiro", "Documento Corpo de Bombeiros", solicitacao.oficio_bombeiro),
    ]

    for tipo, nome, arquivo in campos:
        if arquivo and arquivo.name and os.path.exists(arquivo.path):
            documentos.append({
                "nome": nome,
                "url": reverse("abrir_documento_solicitacao", args=[solicitacao.id, tipo]),
            })

    return render(
        request,
        "gestao/visualizar_documentos.html",
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
        ("bombeiro", "Documento Corpo de Bombeiros", solicitacao.oficio_bombeiro),
    ]

    for tipo, nome, arquivo in campos:

        if arquivo and arquivo.name:

            existe = os.path.exists(arquivo.path)

            documentos.append({
                "nome": nome,
                "url": reverse(
                    "abrir_documento_solicitacao",
                    args=[solicitacao.id, tipo]
                ) if existe else "",
                "arquivo": arquivo.name,
                "existe": existe,
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
def visualizar_documentos(request, id):

    solicitacao = get_object_or_404(
        Solicitacao,
        id=id
    )

    documentos = []

    campos = [
        ("Documento Sanitário", solicitacao.documento_sanitario),
        ("Documento Meio Ambiente", solicitacao.documento_meio_ambiente),
        ("Documento Corpo de Bombeiros", solicitacao.oficio_bombeiro),
    ]

    for nome, arquivo in campos:

        if arquivo and arquivo.name and os.path.exists(arquivo.path):

            documentos.append({
                "nome": nome,
                "url": arquivo.url,
            })

    return render(
        request,
        "gestao/visualizar_documentos.html",
        {
            "solicitacao": solicitacao,
            "documentos": documentos,
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
from datetime import date

@login_required
def agenda_gestao(request):

    eventos = Solicitacao.objects.filter(
        data_evento__gte=date.today()
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

            return redirect("listar_pendentes_opo")

    else:
        form = SolicitacaoManualForm()

    return render(
        request,
        "gestao/lancamento_manual.html",
        {
            "form": form
        }
    )
    )
