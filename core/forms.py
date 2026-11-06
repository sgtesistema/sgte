from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password 
from django.core.exceptions import ValidationError 
from .models import Aluno

class AlunoForm(forms.ModelForm):
    """
    Formulário responsável pelo cadastro de novos alunos.
    Ele atua de forma híbrida: coleta dados para o modelo nativo de autenticação (User)
    e para o modelo de perfil acadêmico (Aluno) simultaneamente.
    """
    
    # Campos extras que não pertencem diretamente ao modelo Aluno, mas ao modelo User do Django.
    # Utilizamos o widget TextInput e PasswordInput injetando classes do Bootstrap (form-control)
    # para garantir que a interface fique responsiva e padronizada.
    username = forms.CharField(max_length=150, required=True, label="Nome de Usuário", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Escolha um nome sem espaços'}))
    senha = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mínimo de 8 caracteres'}))

    class Meta:
        # Vincula este formulário ao modelo Aluno
        model = Aluno
        # Define quais campos do modelo Aluno aparecerão na tela
        fields = ['nome', 'matricula']
        # Mapeia os campos do banco de dados para os elementos HTML visuais
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Seu nome completo'}),
            'matricula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2024001'}),
        }

    # --- FUNÇÃO DE SEGURANÇA (Validação de Campo Customizada) ---
    # No Django, métodos nomeados como 'clean_<nome_do_campo>' são executados automaticamente
    # durante a validação do formulário (quando chamamos form.is_valid()).
    def clean_senha(self):
        senha = self.cleaned_data.get('senha')
        
        # A função validate_password aplica as regras de segurança nativas do Django 
        # (ex: checar se a senha é muito curta, comum ou inteiramente numérica).
        try:
            validate_password(senha)
        except ValidationError as e:
            # Se a senha for considerada fraca, interrompe o processo e devolve
            # a mensagem de erro específica para ser exibida em vermelho no HTML.
            raise forms.ValidationError(e.messages) 
            
        return senha

    # --- SOBRESCRITA DO MÉTODO SAVE ---
    # Interceptamos o processo de salvamento para criar o usuário de autenticação
    # ANTES de salvar o perfil do aluno no banco de dados.
    def save(self, commit=True):
        # 1. Cria a credencial de login com a senha já protegida por hash (PBKDF2/SHA-256)
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['senha']
        )
        
        # 2. Prepara o objeto Aluno em memória, mas pausa o salvamento no banco (commit=False)
        aluno = super().save(commit=False)
        
        # 3. Estabelece o relacionamento OneToOne, vinculando o aluno ao usuário recém-criado
        aluno.user = user

        # 4. Finalmente, salva a entidade completa no banco de dados
        if commit:
            aluno.save()

        return aluno