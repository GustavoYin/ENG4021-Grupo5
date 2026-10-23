"""BioForm Health OS — Etapa 1: rotas e views que renderizam as telas (sem banco de dados)."""
from flask import Flask, redirect, render_template, url_for

from conteudo_legal import ATUALIZADO_EM, PRIVACIDADE, TERMOS

app = Flask(__name__)

# Dados de exemplo só para desenhar a lista. Na etapa com banco, virão da tabela "usuarios".
USUARIOS_EXEMPLO = [
    {"id": 1, "nome": "Edson Silva", "email": "edson@email.com", "objetivo": "Perder peso", "cor": "flame", "cadastro": "02/10/2026"},
    {"id": 2, "nome": "Marina Costa", "email": "marina.costa@email.com", "objetivo": "Ganhar massa", "cor": "violet", "cadastro": "03/10/2026"},
    {"id": 3, "nome": "Lucas Pinho", "email": "lucas.pinho@email.com", "objetivo": "Manter o peso", "cor": "water", "cadastro": "05/10/2026"},
    {"id": 4, "nome": "Ana Beatriz Souza", "email": "ana.souza@email.com", "objetivo": "Saúde e bem-estar", "cor": "green", "cadastro": "06/10/2026"},
    {"id": 5, "nome": "Rafael Mendes", "email": "rafael.mendes@email.com", "objetivo": "Ganhar massa", "cor": "violet", "cadastro": "07/10/2026"},
]


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/cadastro")
def cadastro():
    return render_template("cadastro.html")


@app.route("/esqueci-senha")
def esqueci_senha():
    return render_template("esqueci-senha.html")


@app.route("/perfil/1-dados")
def perfil_dados():
    return render_template("perfil-1-dados.html")


@app.route("/perfil/2-objetivo")
def perfil_objetivo():
    return render_template("perfil-2-objetivo.html")


@app.route("/perfil/3-esportes")
def perfil_esportes():
    return render_template("perfil-3-esportes.html")


@app.route("/perfil/4-resultado")
def perfil_resultado():
    return render_template("perfil-4-resultado.html")


@app.route("/usuarios")
def usuarios():
    return render_template("usuarios.html", usuarios=USUARIOS_EXEMPLO)


@app.route("/termos")
def termos():
    return render_template("legal.html", titulo="Termos de Uso", secoes=TERMOS, atualizado_em=ATUALIZADO_EM)


@app.route("/privacidade")
def privacidade():
    return render_template("legal.html", titulo="Política de Privacidade", secoes=PRIVACIDADE, atualizado_em=ATUALIZADO_EM)


if __name__ == "__main__":
    app.run(debug=True)
