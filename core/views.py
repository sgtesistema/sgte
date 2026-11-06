from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Turma, Aluno
from .forms import AlunoForm

# --- CONTROLE DE ACESSO (Autenticação) ---
# O decorator @login_required atua como um middleware de segurança. 
# Se um usuário não autenticado tentar acessar esta rota, ele será interceptado e 
# redirecionado automaticamente para a tela de login.
@login_required
def index(request):
    """
    View principal do sistema (Dashboard).
    Implementa um Controle de Acesso Baseado em Papéis (RBAC - Role-Based Access Control),
    renderizando interfaces e lógicas diferentes dependendo do nível de privilégio do usuário logado.
    """
    
    # --- FLUXO 1: VISÃO GERENCIAL (DIRETOR/PROFESSOR) ---
    # Verifica se o usuário autenticado possui as *flags* de administração.
    if request.user.is_superuser or request.user.is_staff:
        turmas = Turma.objects.all()
        # Retorna o template injetando a flag 'is_admin' como True para adaptar o front-end
        return render(request, 'core/index.html', {'is_admin': True, 'turmas': turmas})
    
    # --- FLUXO 2: VISÃO DO ALUNO (AUTOATENDIMENTO) ---
    else:
        # Recupera o perfil acadêmico vinculado ao usuário de autenticação atual
        aluno = Aluno.objects.get(user=request.user)
        
        # 1. PROCESSAMENTO DE MATRÍCULA (Requisição POST)
        if request.method == 'POST':
            turma_id = request.POST.get('turma_id')
            if turma_id:
                turma_escolhida = Turma.objects.get(id=turma_id)
                
                # --- REGRA DE NEGÓCIO: VALIDAÇÃO DE VAGAS ---
                # Gatilho de segurança: Verifica se a turma aceita matrículas e 
                # garante que o aluno não tente se matricular em uma turma que já possui.
                if turma_escolhida.status_aberta and turma_escolhida not in aluno.turmas.all():
                    aluno.turmas.add(turma_escolhida) # Vincula o aluno à turma (Many-to-Many)
                    
                    # --- AUTOMAÇÃO DE PROCESSO (Fechamento Automático) ---
                    # Após a inserção, o sistema conta a quantidade atual de alunos.
                    # Se atingiu ou ultrapassou o limite máximo estabelecido no modelo,
                    # a turma é automaticamente trancada no banco de dados.
                    if turma_escolhida.alunos.count() >= turma_escolhida.limite_maximo:
                        turma_escolhida.status_aberta = False
                        turma_escolhida.save()
                        
                    messages.success(request, f"Matrícula realizada na turma {turma_escolhida.nome} com sucesso!")
                else:
                    messages.error(request, "Não foi possível realizar a matrícula. Turma lotada ou você já está matriculado nela.")
            return redirect('index')

        # 2. PREPARAÇÃO DE DADOS PARA A VITRINE (Requisição GET)
        minhas_turmas = aluno.turmas.all()
        
        # --- OTIMIZAÇÃO DE QUERY (QuerySet Filtering) ---
        # Filtra no banco apenas as turmas abertas e exclui (exclude) dinamicamente 
        # aquelas cujos IDs já constam na lista de turmas do aluno logado.
        turmas_disponiveis = Turma.objects.filter(status_aberta=True).exclude(id__in=minhas_turmas.values_list('id', flat=True))
        
        return render(request, 'core/index.html', {
            'is_admin': False, 
            'aluno': aluno, 
            'minhas_turmas': minhas_turmas, 
            'turmas_disponiveis': turmas_disponiveis
        })


# --- FUNÇÃO DE CADASTRO DO ALUNO (TELA PÚBLICA) ---
def cadastrar_aluno(request):
    """
    Endpoint público para auto-cadastro de novos discentes.
    Trata tanto a exibição do formulário vazio (GET) quanto o processamento dos dados (POST).
    """
    if request.method == 'POST':
        form = AlunoForm(request.POST)
        if form.is_valid():
            # A validação e o salvamento em cascata (User + Aluno) ocorrem dentro do forms.py
            form.save() 
            messages.success(request, 'Cadastro realizado com sucesso!')
            return redirect('/accounts/login/') # Redirecionamento Pós-Post (PRG Pattern)
    else:
        form = AlunoForm()

    return render(request, 'core/cadastrar_aluno.html', {'form': form})


# --- FUNÇÃO PARA GERAR O RELATÓRIO DA TURMA ---
@login_required
def relatorio_turma(request, turma_id):
    """
    Módulo de exportação de dados acadêmicos.
    Gera uma lista formatada para impressão, exigindo privilégios administrativos.
    """
    # --- AUTORIZAÇÃO (Authorization) ---
    # Mesmo estando logado (@login_required), validamos se o usuário tem o papel adequado.
    # Se um aluno comum tentar acessar a URL do relatório digitando diretamente no navegador, ele será bloqueado.
    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Acesso negado.")
        return redirect('index')
    
    # --- TRATAMENTO DE EXCEÇÕES (Robustez) ---
    # get_object_or_404 previne erros 500 (Internal Server Error) caso a turma_id passada na URL não exista.
    # O Django intercepta a falha de banco e retorna uma página 404 (Not Found) amigável.
    turma = get_object_or_404(Turma, id=turma_id)
    
    # --- ORDENAÇÃO A NÍVEL DE BANCO DE DADOS ---
    # O método 'order_by' instrui o banco relacional (ex: PostgreSQL/SQLite) a realizar a 
    # ordenação alfabética antes de devolver os dados, sendo mais performático que ordenar via Python.
    alunos = turma.alunos.all().order_by('nome')
    
    return render(request, 'core/relatorio_turma.html', {'turma': turma, 'alunos': alunos})