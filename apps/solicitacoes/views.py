from django.shortcuts import render, get_object_or_404, redirect
from .models import Solicitacao, MatriculaAutorizada
import os
import base64
from io import BytesIO
from datetime import date, timedelta
from pathlib import Path
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
import openpyxl
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import MatriculaAutorizada



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

    eventos_hoje = Solicitacao.objects.filter(
        data_evento=date.today()
    ).order_by(
        "hora_inicio",
        "nome_evento"
    )

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
            "eventos_hoje": eventos_hoje,
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
def corrigir_solicitacao(request, id):

    solicitacao = get_object_or_404(
        Solicitacao,
        id=id
    )

    # Só permite edição quando a solicitação estiver em correção
    if solicitacao.status != "CORRECAO":
        messages.error(
            request,
            "Esta solicitação não está disponível para correção."
        )
        return redirect("consultar_protocolo")

    if request.method == "POST":

        form = SolicitacaoForm(
            request.POST,
            request.FILES,
            instance=solicitacao
        )

        if form.is_valid():

            obj = form.save(commit=False)

            # Mantém o mesmo ID e protocolo
            # e devolve a solicitação para nova análise
            obj.status = "PENDENTE"

            obj.save()

            messages.success(
                request,
                "Correções enviadas com sucesso. "
                "Sua solicitação será analisada novamente."
            )

            return redirect(
                f"/consultar/?protocolo={obj.protocolo}"
            )

    else:

        form = SolicitacaoForm(
            instance=solicitacao
        )

    return render(
        request,
        "solicitacoes/corrigir_solicitacao.html",
        {
            "form": form,
            "solicitacao": solicitacao,
            "modo_correcao": True,
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

    pendentes_opo = Solicitacao.objects.filter(
        status="PENDENTE"
    ).count()

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
    ).order_by("data_evento", "hora_inicio")[:5]

    usuarios = User.objects.all().count()

    return render(
        request,
        "gestao/painel_gestao.html",
        {
            "pendentes_opo": pendentes_opo,
            "eventos_semana": eventos_semana,
            "eventos_mes": eventos_mes,
            "proximos_eventos": proximos_eventos,
            "usuarios": usuarios,
        }
    )


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

    solicitacao = get_object_or_404(Solicitacao, id=id)

    documentos = [
        {
            "nome": "Documento Sanitário",
            "tipo": "sanitario",
            "arquivo": solicitacao.documento_sanitario,
        },
        {
            "nome": "Documento Meio Ambiente",
            "tipo": "meio_ambiente",
            "arquivo": solicitacao.documento_meio_ambiente,
        },
        {
            "nome": "Ofício ao Comandante",
            "tipo": "comandante",
            "arquivo": solicitacao.oficio_comandante,
        },
        {
            "nome": "Documento Corpo de Bombeiros",
            "tipo": "bombeiro",
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
def opos_geradas(request):
    pasta_protocolos = Path(settings.MEDIA_ROOT) / "protocolos"

    protocolos = []

    if pasta_protocolos.exists():
        for pasta in pasta_protocolos.iterdir():
            if pasta.is_dir():
                arquivos = []

                for arquivo in pasta.iterdir():
                    if arquivo.is_file() and arquivo.suffix.lower() == ".pdf":
                        arquivos.append({
                            "nome": arquivo.name,
                            "url": f"{settings.MEDIA_URL}protocolos/{pasta.name}/{arquivo.name}",
                        })

                protocolos.append({
                    "codigo": pasta.name,
                    "arquivos": arquivos,
                })

    protocolos = sorted(protocolos, key=lambda x: x["codigo"])

    return render(request, "gestao/opos_geradas.html", {
    "protocolos": protocolos,
})
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



def validar_matricula_opo_publica(request, id):
    solicitacao = get_object_or_404(
        Solicitacao,
        id=id,
        status="APROVADO"
    )

    if request.method == "POST":
        matricula = request.POST.get("matricula", "").strip()

        if MatriculaAutorizada.objects.filter(
            matricula=matricula,
            ativo=True
        ).exists():
            request.session[f"opo_publica_autorizada_{id}"] = True
            return redirect("detalhe_opo_publica", id=id)

        messages.error(request, "Matrícula não autorizada.")

    return render(request, "consulta/validar_matricula_opo.html", {
        "solicitacao": solicitacao
    })
def detalhe_opo_publica(request, id):
    if not request.session.get(f"opo_publica_autorizada_{id}"):
        return redirect("validar_matricula_opo_publica", id=id)

    solicitacao = get_object_or_404(
        Solicitacao,
        id=id,
        status="APROVADO"
    )

    return render(request, "consulta/detalhe_opo_publica.html", {
        "solicitacao": solicitacao
    })

def solicitar_correcao(request, id):

    solicitacao = get_object_or_404(Solicitacao, id=id)

    mensagem = f"""
Prezado(a) {solicitacao.solicitante},

Após análise da documentação referente ao evento:
{solicitacao.nome_evento}

Informamos que sua Ordem de Policiamento Operacional (OPO)
não pôde ser gerada.

Motivo:

• erro no cadastro;
• Data no ofício diferente da solicitação;
• duplicidade da solicitação;
• ausência de documentos obrigatórios.

Solicitamos que compareça à sede da 95ª CIPM para regularizar as pendências.
Após a regularização, uma nova análise será realizada.

Atenciosamente,

Seção de Planejamento Operacional
"""

    send_mail(
        subject="Pendência na Solicitação de Ordem de Policiamento",
        message=mensagem,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[solicitacao.email],
        fail_silently=False,
    )

    solicitacao.status = "CORRECAO"
    solicitacao.save()

    messages.success(
        request,
        "Solicitante notificado por e-mail."
    )

    return redirect("listar_pendentes_opo")


def importar_matriculas_painel(request):
    if request.method == "POST":
        arquivo = request.FILES.get("arquivo")

        if not arquivo:
            messages.error(request, "Selecione um arquivo Excel.")
            return redirect("importar_matriculas_painel")

        if not arquivo.name.endswith(".xlsx"):
            messages.error(request, "Envie apenas arquivo .xlsx.")
            return redirect("importar_matriculas_painel")

        wb = openpyxl.load_workbook(arquivo)
        ws = wb.active

        criadas = 0
        atualizadas = 0

        # pula cabeçalho
        for linha in ws.iter_rows(min_row=2, values_only=True):
            matricula = linha[0]
            nome = linha[1] if len(linha) > 1 else ""
            posto = linha[2] if len(linha) > 2 else ""
            unidade = linha[3] if len(linha) > 3 else "95ª CIPM"

            if not matricula:
                continue

            obj, criado = MatriculaAutorizada.objects.update_or_create(
                matricula=str(matricula).strip(),
                defaults={
                    "nome": str(nome).strip() if nome else "",
                    "posto": str(posto).strip() if posto else "",
                    "unidade": str(unidade).strip() if unidade else "95ª CIPM",
                    "ativo": True,
                }
            )

            if criado:
                criadas += 1
            else:
                atualizadas += 1

        messages.success(
            request,
            f"Importação concluída. Criadas: {criadas}. Atualizadas: {atualizadas}."
        )

        return redirect("importar_matriculas_painel")

    return render(request, "gestao/importar_matriculas.html")
