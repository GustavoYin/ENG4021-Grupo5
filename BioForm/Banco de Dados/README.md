# BioForm — banco de dados (Django)

Tabelas criadas a partir de `App Saúde/modelagemDados.txt`, seguindo a aula
*Atividade 03 — Modelagem de Dados*. Projeto Django `bioform`, app `saude`
(as tabelas estão em `saude/models.py` e as telas do admin em `saude/admin.py`).

| Domínio | Tabelas |
|---|---|
| Identidade e perfil | `usuarios`, `esportes`, `esportes_usuario` |
| Evolução | `historico_medidas` |
| Nutrição | `metas_nutricionais`, `catalogo_alimentos`, `medidas_caseiras`, `refeicoes_personalizadas`, `refeicoes_personalizadas_itens`, `diario_consumo`, `registros_refeicao`, `registros_refeicao_itens` |
| Treino e atividades | `fichas_treino`, `exercicios_ficha`, `sessoes_atividade`, `series_executadas_historico` |
| Gamificação social | `perfil_gamificacao`, `historico_xp`, `amizades`, `grupos`, `membros_grupo`, `desafios`, `participantes_desafio` |

## Como rodar

```bash
cd "BioForm/Banco de Dados"
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac/Replit: source .venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate        # cria as tabelas e já popula alimentos, esportes e medidas caseiras
python manage.py createsuperuser
python manage.py runserver
```

Site: http://127.0.0.1:8000/ (cadastro, login e perfil) · Admin: http://127.0.0.1:8000/admin/

Para ver a listagem de usuários (`/usuarios/`), entre com uma conta marcada como *equipe* (staff) no admin.
O link de "Esqueci minha senha" é impresso no terminal do `runserver` (não há servidor de e-mail configurado).

Testes: `python manage.py test saude`

## Dados que já vêm carregados

**Alimentos** (`0002_popular_alimentos_taco`): **591 alimentos** da
**TACO — Tabela Brasileira de Composição de Alimentos** (NEPA/UNICAMP, 4ª ed., 2011),
com kcal, proteína, carboidrato e gordura **por 100 g**.

- Dados: `saude/dados/alimentos_taco.csv` (extraído de
  [raulfdm/taco-api](https://github.com/raulfdm/taco-api), licença MIT).
- Valores ausentes na TACO por serem traço ou "não se aplica" (ex.: proteína do azeite) foram gravados como 0.
- 6 alimentos sem nenhuma análise na TACO ficaram de fora (ex.: leite integral, coco verde).

**Esportes** (`0003_popular_esportes`): os 10 esportes do mockup e das regras de negócio, com um
MET de referência aproximado (Compendium of Physical Activities) para o cálculo do gasto.
Dá para ajustar os valores pelo admin.

**Medidas caseiras** (`0004_popular_medidas_caseiras`): **97 medidas** (colher, concha, escumadeira,
fatia, unidade, copo...) para **69 alimentos** comuns da TACO (arroz, feijão, frango, ovo, pão francês,
frutas, azeite...). Os gramas são **aproximados**, para uma porção média, no estilo das tabelas de medidas
caseiras usadas em nutrição. Dá para corrigir ou acrescentar pelo admin.

Rodar `migrate` de novo não duplica nada (cada registro tem UUID fixo).

## Regras que já estão no banco

- Um diário de consumo por usuário por dia; um perfil de gamificação por usuário.
- Amizade sem par repetido e sem amizade consigo mesmo; um esporte só uma vez por perfil.
- Desafio não pode terminar antes de começar; CPF com 11 números.
- `RegistroRefeicaoItem.macros()` calcula kcal e macros do que foi comido (em medida caseira ou porção).
- `Grupo.ranking_semanal(dia)` ordena os membros pelo XP da semana (segunda a domingo).
- `PerfilGamificacao.nivel()` devolve o patamar (Semente, Bronze, Prata, Ouro, Diamante).

## Telas (Sprint 6)

Usam o visual de `App Saúde/Mockup Login` (login, cadastro e perfil) e o `usuarios.css` da pasta
`usuários/` (editar perfil e listagem). Os CSS foram copiados para `saude/static/saude/css/`.

| Endereço | Tela |
|---|---|
| `/cadastro/` | Cria a conta (e-mail + senha) e o perfil (nome, CPF, celular) e já entra |
| `/entrar/`, `/sair/` | Login com **e-mail ou CPF**, "Lembrar de mim" e logout |
| `/senha/esqueci/` | Recuperação de senha por link (token do Django) |
| `/perfil/dados/` → `/objetivo/` → `/esportes/` → `/metas/` | Onboarding em 4 passos; depois servem para editar |
| `/conta/` | Editar perfil (nome, apelido, e-mail, celular), trocar senha e excluir conta |
| `/usuarios/` | Listagem com busca, filtro e paginação (só equipe/staff) |

- Validação repetida no servidor (`saude/forms.py`): CPF com dígitos verificadores, CPF e e-mail únicos,
  senha pelas regras do Django, idade mínima de 14 anos, termos aceitos.
- Login por e-mail ou CPF: `saude/backends.py`.
- Não dá para pular passos do onboarding: cada página manda para o primeiro passo que falta.
- Mudar peso, objetivo ou esportes recalcula a meta na hora. Peso novo em outro dia vira um novo ponto
  do histórico (gráfico de evolução); no mesmo dia, corrige o registro do dia.
- `templates/404.html`: página de erro no visual do app (aparece com `DEBUG = False`).
- A migração `0005` deixou nascimento, sexo, altura e biotipo opcionais no banco, porque a conta é
  criada antes do onboarding. Os formulários continuam exigindo esses campos.

## Calculadora de metas (`saude/metas.py`)

Fórmulas do mockup `perfil-4-resultado.html`:

- **TMB** (Mifflin-St Jeor): 10 × peso + 6,25 × altura − 5 × idade + 5 (homens) ou − 161 (mulheres).
- **Esportes**: (MET × fator da intensidade − 1) × peso × 1 h × vezes por semana ÷ 7.
  Fator: leve 0,8 · moderada 1,0 · intensa 1,2 · máxima 1,4. Desconta 1 MET porque o repouso já está na TMB.
  Cada sessão conta como 1 hora, porque o perfil ainda não guarda a duração dos treinos.
- **Atividade diária e digestão**: NEAT (15% da TMB) + efeito térmico dos alimentos (10% do gasto).
- **Meta** = TDEE − 500 (perder peso), + 400 (hipertrofia) ou ± 0 (manutenção e saúde), **nunca abaixo da TMB**.
- **Proteína**: 2,1 g/kg (perder) · 2,0 (hipertrofia) · 1,8 (manutenção) · 1,6 (saúde). **Gordura**: 0,8 g/kg.
  **Carboidrato**: o que sobra das calorias ÷ 4. **Água**: 35 ml/kg.
- O "Na prática" usa o catálogo TACO (frango e arroz) e a medida caseira da colher de azeite.
- Grava em `metas_nutricionais` (uma meta por usuário por dia).
- O biotipo é salvo, mas não entra na conta (não há fórmula validada para isso).

## Ainda falta

- Medidas caseiras dos outros ~520 alimentos (hoje só os 69 mais comuns têm).
- Foto de perfil (o modelo guarda uma URL, mas o projeto ainda não tem upload de arquivos).
- Duração dos treinos no perfil, para o gasto dos esportes não depender da média de 1 hora.
- Não modelados: diário de bem-estar (humor, dores, sono) e lembretes (RF16).
