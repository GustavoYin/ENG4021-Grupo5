"""Login pelo e-mail OU pelo CPF ("E-mail ou CPF" na tela de entrar)."""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from .forms import so_digitos

User = get_user_model()


class EmailOuCPFBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or password is None:
            return None
        identificador = username.strip()
        cpf = so_digitos(identificador)
        if '@' not in identificador and len(cpf) == 11:
            conta = User.objects.filter(usuario__cpf=cpf).first()
        else:
            conta = User.objects.filter(email__iexact=identificador).first()

        if conta is None:
            # Gasta o mesmo tempo de quando a conta existe, para não revelar quais e-mails estão cadastrados
            User().set_password(password)
            return None
        if conta.check_password(password) and self.user_can_authenticate(conta):
            return conta
        return None
