from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class Turma(models.Model):
    """
    Entidade principal que representa uma Turma Especial no sistema.
    Mapeada pelo ORM do Django para a respectiva tabela no banco de dados.
    """
    
    # Enumeração para restringir as opções de período no banco de dados (Data Integrity).
    PERIODOS = [
        ('M', 'Manhã'),
        ('T', 'Tarde'),
        ('N', 'Noite')
    ]

    nome = models.CharField(max_length=50, help_text="Ex: 3º Ano B")
    periodo = models.CharField(max_length=20, choices=PERIODOS)
    
    # --- INTEGRIDADE REFERENCIAL E SEGURANÇA (RBAC) ---
    # Chave estrangeira (1:N) que vincula a turma a um usuário do sistema.
    # A propriedade 'limit_choices_to={'is_staff': True}' é um filtro de segurança a nível 
    # de banco de dados: impede que alunos comuns sejam designados como professores da turma.
    professor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, # Se o professor for excluído do sistema, a turma não é apagada (fica null)
        null=True, 
        blank=True, 
        limit_choices_to={'is_staff': True}, 
        help_text="Professor responsável por esta turma"
    )
    
    # Campos que controlam a regra de negócio de ocupação e disponibilidade da turma.
    limite_minimo = models.IntegerField(default=10, help_text="Mínimo de alunos para a turma funcionar")
    limite_maximo = models.IntegerField(default=30, help_text="Máximo de vagas da turma")
    status_aberta = models.BooleanField(default=True, help_text="Marcado = Aceita matrículas")

    def __str__(self):
        # Representação textual do objeto para as interfaces do painel administrativo
        return f"{self.nome} - {self.get_periodo_display()} (Vagas: {self.limite_maximo})"

    # --- VALIDAÇÃO A NÍVEL DE MODELO (Business Rules) ---
    # O método 'clean' é invocado antes de salvar o objeto no banco de dados.
    # Ele garante a consistência lógica: é impossível criar uma turma onde o limite mínimo seja maior que o máximo.
    def clean(self):
        if self.limite_minimo > self.limite_maximo:
            raise ValidationError('O limite mínimo não pode ser maior que o limite máximo.')


class Aluno(models.Model):
    """
    Entidade que representa o Perfil Acadêmico do discente.
    """
    
    # --- EXTENSÃO DO MODELO DE AUTENTICAÇÃO ---
    # Relacionamento Um-para-Um (1:1) com o modelo 'User' nativo do Django.
    # Esta arquitetura permite utilizar o sistema robusto de login/senha do framework,
    # adicionando campos acadêmicos específicos (nome, matricula) sem alterar o core do Django.
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    
    nome = models.CharField(max_length=100)
    
    # unique=True: Restrição de banco de dados (Constraint) que impede matrículas duplicadas.
    matricula = models.CharField(max_length=20, unique=True)
    
    # --- CARDINALIDADE MUITOS-PARA-MUITOS (N:N) ---
    # Um aluno pode estar matriculado em várias turmas, e uma turma comporta vários alunos.
    # O Django cria automaticamente uma tabela associativa no banco de dados para gerenciar isso.
    # A propriedade 'related_name='alunos'' permite realizar a busca reversa (Ex: turma.alunos.all()).
    turmas = models.ManyToManyField(Turma, blank=True, related_name='alunos')

    def __str__(self):
        return f"{self.nome} ({self.matricula})"