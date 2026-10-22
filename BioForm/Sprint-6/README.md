# BioForm — Sprint 6

Combinação escolhida: **1 difícil + 2 médias**. Tudo foi feito dentro do projeto Django em
`BioForm/Banco de Dados` (app `saude`), com testes automatizados.

- **Difícil — Autenticação real e telas de usuário no Django.**
  Cadastro (conta + perfil), login por e-mail **ou** CPF, "Lembrar de mim", logout, recuperação de senha
  por link, onboarding do perfil em 4 passos, editar perfil, trocar senha, excluir conta e listagem de
  usuários com busca/filtro/paginação (só equipe). As telas usam o visual de `App Saúde/Mockup Login`
  e o `usuarios.css` de `usuários/`. A validação que antes era só no navegador agora é repetida no
  servidor (CPF com dígitos verificadores, CPF/e-mail únicos, regras de senha do Django).
  Código: `saude/views.py`, `saude/forms.py`, `saude/backends.py`, `saude/urls.py`, `saude/templates/`.

- **Média — Medidas caseiras (RF10).**
  Migração `0004_popular_medidas_caseiras` com 97 medidas (colher, concha, fatia, unidade, copo...) para
  os 69 alimentos mais comuns da TACO. A tabela estava vazia; agora dá para registrar "3 colheres de
  arroz" ou "1 concha de feijão" e o banco calcula kcal e macros.

- **Média — Calculadora de metas nutricionais (RF15/RF20).**
  `saude/metas.py` implementa as fórmulas descritas no mockup `perfil-4-resultado.html` (TMB de
  Mifflin-St Jeor + gasto dos esportes pelo MET + objetivo), gera proteína, carboidrato, gordura e água
  e salva em `metas_nutricionais`. A tela "Suas metas estão prontas!" deixou de ser um exemplo fixo e
  mostra a conta de verdade de cada usuário; mudar peso, objetivo ou esportes recalcula na hora.

## Como testar

```bash
cd "BioForm/Banco de Dados"
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py test saude      # 42 testes
python manage.py runserver       # abra http://127.0.0.1:8000/ e crie uma conta
```

Detalhes das telas, regras e fórmulas: `BioForm/Banco de Dados/README.md`.
