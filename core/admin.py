from django.contrib import admin
from .models import Aluno, Turma

@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    """
    Configurações da interface de gerenciamento do modelo Turma no painel Admin.
    """
    
    # list_display: Define exatamente quais colunas aparecerão na tabela de listagem geral.
    # Isso evita que o administrador precise abrir registro por registro para ver as informações.
    list_display = ['nome', 'periodo', 'professor', 'status_aberta', 'limite_minimo', 'limite_maximo']
    
    # list_filter: Cria um menu lateral na direita permitindo filtrar os registros.
    # Ex: O diretor pode clicar em "Status aberta" para ver apenas as turmas com vagas.
    list_filter = ['periodo', 'status_aberta']
     
    # search_fields: Adiciona uma barra de pesquisa no topo da página.
    # Permite buscar turmas rapidamente digitando o nome.
    search_fields = ['nome']

@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    """
    Configurações da interface de gerenciamento do modelo Aluno no painel Admin.
    """
    
    # list_display: Define as colunas visíveis na tabela de alunos. 
    # Como campos ManyToMany (turmas) não funcionam nativamente no display, chamamos a função 'get_turmas'.
    list_display = ['nome', 'matricula', 'get_turmas'] 
    
    # list_filter: Cria um filtro lateral no painel. 
    # Permite que a direção selecione uma turma específica e veja rapidamente todos os alunos matriculados nela.
    list_filter = ['turmas'] 
    
    # search_fields: Habilita a barra de busca superior. 
    # O diretor pode localizar um aluno pesquisando pelo nome ou pelo número exato da matrícula.
    search_fields = ['nome', 'matricula']

    # --- FUNÇÃO PERSONALIZADA (Custom Method) ---
    # Campos com relação Muitos-para-Muitos (ManyToManyField) não podem ser listados diretamente.
    # Esta função percorre todas as turmas vinculadas ao aluno (obj.turmas.all()) 
    # e retorna os nomes das turmas formatados em texto, separados por vírgula.
    def get_turmas(self, obj):
        return ", ".join([t.nome for t in obj.turmas.all()])
    
    # short_description: Sobrescreve o nome da função que aparece no cabeçalho 
    # da coluna na tabela de listagem do painel administrativo, tornando-o amigável.
    get_turmas.short_description = 'Turmas Matriculadas'