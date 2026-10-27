# BioForm: banco de dados (Django)

Tabelas criadas a partir de `App Saúde/modelagemDados.txt`, seguindo a aula **Atividade 03: Modelagem de Dados**.

O projeto Django se chama `bioform`. As tabelas principais estão no app `saude`, em `saude/models.py`, e as telas do admin em `saude/admin.py`.

## Sumário

- [Apps do projeto](#apps-do-projeto)
- [Tabelas](#tabelas)
- [Como rodar](#como-rodar)
- [Testes](#testes)
- [Dados que já vêm carregados](#dados-que-já-vêm-carregados)
- [Regras que já estão no banco](#regras-que-já-estão-no-banco)
- [Métodos dos modelos](#métodos-dos-modelos)
- [Bem-estar](#bem-estar)
- [Lembretes](#lembretes)

## Apps do projeto

| App | O que faz | Onde fica |
|---|---|---|
| `saude` | tabelas principais do banco e as telas do admin | `BioForm/Banco de Dados` |
| `contas` | login, cadastro e perfil | `BioForm/Banco de Dados` |
| `diario` | diário de consumo | `BioForm/Sprint-6` |
| `medidas_caseiras` | medidas caseiras dos alimentos | `BioForm/Sprint-6` |
| `metas` | metas nutricionais | `BioForm/Sprint-6` |
| `bem_estar` | diário de bem-estar: humor, sono e dores | ao lado de `diario`, `medidas_caseiras` e `metas` |
| `lembretes` | lembretes de treino, refeição, água e pesagem (RF16) | ao lado de `diario`, `medidas_caseiras` e `metas` |

Os apps de `Sprint-6`, `bem_estar` e `lembretes` são carregados por `bioform/settings.py`.

## Tabelas

São 27 tabelas, organizadas em sete domínios.

| Domínio | Tabelas |
|---|---|
| Identidade e perfil | `usuarios`, `esportes`, `esportes_usuario` |
| Evolução | `historico_medidas` |
| Nutrição | `metas_nutricionais`, `catalogo_alimentos`, `medidas_caseiras`, `refeicoes_personalizadas`, `refeicoes_personalizadas_itens`, `diario_consumo`, `registros_refeicao`, `registros_refeicao_itens` |
| Treino e atividades | `fichas_treino`, `exercicios_ficha`, `sessoes_atividade`, `series_executadas_historico` |
| Gamificação social | `perfil_gamificacao`, `historico_xp`, `amizades`, `grupos`, `membros_grupo`, `desafios`, `participantes_desafio` |
| Bem-estar | `diario_bem_estar`, `registros_dor` |
| Lembretes (RF16) | `lembretes`, `lembretes_enviados` |

## Como rodar

```bash
cd "BioForm/Banco de Dados"
python -m venv .venv
.venv\Scripts\activate          # Windows (Linux/Mac/Replit: source .venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate        # cria as tabelas e já popula alimentos, esportes e medidas caseiras
python manage.py createsuperuser
python manage.py runserver
```

| O quê | Endereço |
|---|---|
| Site | http://127.0.0.1:8000/ |
| Admin | http://127.0.0.1:8000/admin/ |

O `createsuperuser` cria o usuário que entra no admin.

## Testes

```bash
python manage.py test saude contas diario medidas_caseiras metas bem_estar lembretes
```

## Dados que já vêm carregados

O `migrate` já popula três conjuntos de dados. Rodar `migrate` de novo **não duplica nada**, porque cada registro tem UUID fixo.

### Alimentos (`0002_popular_alimentos_taco`)

591 alimentos da **TACO** (Tabela Brasileira de Composição de Alimentos, NEPA/UNICAMP, 4ª ed., 2011), com kcal, proteína, carboidrato e gordura por 100 g.

- **Arquivo dos dados:** `saude/dados/alimentos_taco.csv`.
- **Origem:** extraído de [raulfdm/taco-api](https://github.com/raulfdm/taco-api), licença MIT.
- **Valores ausentes:** na TACO, valores "traço" ou "não se aplica" (por exemplo, a proteína do azeite) foram gravados como `0`.
- **Alimentos de fora:** 6 alimentos sem nenhuma análise na TACO não foram incluídos (por exemplo, leite integral e coco verde).

### Esportes (`0003_popular_esportes`)

Os 10 esportes do mockup e das regras de negócio, cada um com um **MET de referência aproximado** (Compendium of Physical Activities) para o cálculo do gasto. Os valores podem ser ajustados pelo admin.

### Medidas caseiras

Populadas junto com o `migrate`.

## Regras que já estão no banco

- Um **diário de consumo** por usuário por dia.
- Um **perfil de gamificação** por usuário.
- Amizade sem par repetido e sem amizade consigo mesmo.
- Um esporte só uma vez por perfil.
- Desafio não pode terminar antes de começar.
- CPF com 11 números.
- Um **diário de bem-estar** por usuário por dia.
- Horas de sono entre 0 e 24, qualidade do sono entre 1 e 5.
- Uma dor por região do corpo por dia, com intensidade entre 0 e 10.
- Um envio de lembrete por dia: o mesmo lembrete não é avisado duas vezes no mesmo dia.
- Nascimento, sexo, altura e biotipo podem ficar **vazios** no banco (migração `0004`), porque a conta é criada antes de o perfil ser preenchido.

## Métodos dos modelos

| Método | O que devolve |
|---|---|
| `RegistroRefeicaoItem.macros()` | kcal e macros do que foi comido, em medida caseira ou porção |
| `Grupo.ranking_semanal(dia)` | membros ordenados pelo XP da semana (segunda a domingo) |
| `PerfilGamificacao.nivel()` | o patamar: Semente, Bronze, Prata, Ouro ou Diamante |
| `Lembrete.vale_para(dia)` | `True` se o lembrete está ativo e programado para o dia da semana informado |
| `lembretes_pendentes(agora)` | lembretes de hoje cujo horário já chegou (dentro da janela) e que ainda não foram enviados |
| `enviar(lembrete, agora)` | envia o lembrete pelo canal escolhido e registra o envio |

## Bem-estar

App `bem_estar`: o usuário registra, por dia, **humor** (1 a 5), **horas e qualidade do sono** e **dores** por região do corpo (intensidade de 0 a 10). Um dia pode ter várias dores, por isso elas ficam em tabela própria (`registros_dor`).

| URL | Tela |
|---|---|
| `/bem-estar/` | registrar ou corrigir o dia (aceita `?data=AAAA-MM-DD`; datas futuras viram hoje) |
| `/bem-estar/historico/` | últimos 60 registros do usuário |

Cada pessoa só vê os próprios registros. O app também está no admin (`diario_bem_estar` com as dores dentro).

## Lembretes

App `lembretes` (RF16). Duas tabelas: `lembretes` guarda a **regra** (tipo, título, mensagem, horário, dias da semana, canal e, nos de treino, a ficha) e `lembretes_enviados` guarda **cada envio**.

| URL | Tela |
|---|---|
| `/lembretes/` | lista dos lembretes (ativar, desativar, editar, excluir) |
| `/lembretes/novo/` | criar lembrete |
| `/lembretes/<id>/editar/` | editar lembrete |
| `/lembretes/recebidos/` | lembretes recebidos, com "marcar todos como lidos" |

### Envio automático

O comando `enviar_lembretes` envia os lembretes cujo horário chegou e grava o envio. Ele precisa rodar de minuto em minuto:

```bash
python manage.py enviar_lembretes            # uma rodada (para o cron ou outro agendador)
python manage.py enviar_lembretes --loop     # fica rodando e verifica a cada 60 segundos
python manage.py enviar_lembretes --janela 30   # tolerância de 30 min (padrão: 60)
```

- **Janela de tolerância:** um lembrete só é enviado até 60 minutos depois do horário marcado. Se o agendador ficar parado, não avisa o treino das 8h às 14h.
- **Sem repetição:** rodar o comando várias vezes não duplica nada, porque cada lembrete tem no máximo um envio por dia.
- **Falha em um lembrete** não trava os outros. Se o e-mail falhar, nada é registrado e a próxima rodada tenta de novo, dentro da janela.
- **Canal "no aplicativo":** o aviso aparece em `/lembretes/recebidos/`.
- **Canal "e-mail":** envia e-mail para o endereço do usuário e também registra o envio. Sem e-mail cadastrado, vale como aviso no aplicativo.

### Configuração em `bioform/settings.py`

```python
INSTALLED_APPS += ["bem_estar", "lembretes"]

TIME_ZONE = "America/Sao_Paulo"   # sem isso o Django usa UTC e os lembretes disparam 3 horas fora do horário
USE_TZ = True

# E-mail em desenvolvimento: imprime a mensagem no terminal em vez de enviar
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAI