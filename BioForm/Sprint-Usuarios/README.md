# BioForm — tarefas da sprint

Implementações independentes em HTML, CSS e JavaScript, para integração posterior.

- **Fácil:** `404.html` — tela para rota inexistente. O servidor ainda precisa configurar o retorno HTTP 404 e ajustar o link inicial.
- **Média:** `cadastro-validacao.html` + `cadastro-validacao.js` — validação de nome, e-mail, senha e confirmação no navegador. A validação precisa ser repetida no servidor.
- **Média:** `editar-perfil.html` — interface de edição com validação HTML nativa. Não salva dados nem altera usuários reais.

## Como testar
Abra os arquivos HTML no navegador. Para testar o cadastro, experimente campos vazios, e-mail inválido, senha com menos de 8 caracteres e confirmação diferente. Para testar a edição, altere nome/e-mail e clique em Salvar.

## Integração
Estes protótipos não usam Flask nem banco de dados. O grupo deverá integrar as páginas às rotas, ao estilo existente e às operações seguras de autenticação e persistência. Não usar senhas reais nos testes.
