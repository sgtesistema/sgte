from django.contrib import admin
from django.urls import path, include
from core import views  # Importa as views do seu app 'core'

urlpatterns = [
    # Rota do painel de administração
    path('admin/', admin.site.urls),
    
    # Rota da página inicial (Painel do Diretor/Aluno)
    path('', views.index, name='index'),
    
    # Rota para o cadastro de novos alunos
    path('cadastrar/', views.cadastrar_aluno, name='cadastrar_aluno'),
    
    # Rota de  Relatório de matrículas da turma
    path('relatorio/turma/<int:turma_id>/', views.relatorio_turma, name='relatorio_turma'),
    
    # Rotas de autenticação padrão do Django (login, logout, etc.)
    path('accounts/', include('django.contrib.auth.urls')),
]