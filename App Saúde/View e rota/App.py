"""BioForm Health OS — rotas e views das telas (login, cadastro, perfil) ligadas ao banco."""
import os
import re
import uuid
from datetime import date
from functools import wraps
from pathlib import Path

from flask import Flask, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import calculos
import database
from database import get_db

BASE = Path(__file__).parent

SEXOS = {"masculino": "Masculino", "feminino": "Feminino"}
BIOTIPOS = {"ectomorfo": "Ectomorfo", "mesomorfo": "Mesomorfo", "endomorfo": "Endomorfo"}
OBJETIVOS = {
    "emagrecimento": "Perder peso", "manutencao": "Manter o peso",
    "hipertrofia": "Ganhar massa", "saude": "Saúde e bem-estar",
}
ESPORTES = {
    "musculacao": "Musculação", "corrida": "Corrida", "ciclismo": "Ciclismo", "natacao": "Natação",
    "funcional": "Funcional", "futebol": "Futebol", "lutas": "Lutas", "yoga": "Yoga",
}
FREQUENCIAS = ["1x", "2x", "3x", "4x", "5x", "6x", "Diário"]
INTENSIDADES = list(calculos.KCAL_SESSAO)
IMAGENS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-troque-em-producao"),
        DATABASE=os.getenv("DATABASE_PATH", str(BASE / "instance" / "bioform.db")),
        UPLOAD_DIR=str(BASE / "static" / "uploads"),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,  # fotos de até 5 MB
    )
    if config:
        app.config.update(config)
    database.init_app(app)
    Path(app.config["UPLOAD_DIR"]).mkdir(parents=True, exist_ok=True)

    # ---------- filtros de formatação (pt-BR) ----------
    app.jinja_env.filters["milhar"] = lambda v: f"{int(v):,}".replace(",", ".")
    app.jinja_env.filters["decimal"] = lambda v: f"{float(v):.1f}".replace(".", ",")

    # ---------- helpers ----------
    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            uid = session.get("usuario_id")
            g.usuario = (
                get_db().execute("SELECT * FROM usuarios WHERE id = ?", (uid,)).fetchone() if uid else None
            )
            if g.usuario is None:
                session.clear()
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped

    def peso_atual(uid):
        row = get_db().execute(
            "SELECT peso_kg FROM historico_medidas WHERE usuario_id = ? "
            "ORDER BY data_registro DESC, rowid DESC LIMIT 1", (uid,)).fetchone()
        return row["peso_kg"] if row else None

    def numero(texto):
        return float(str(texto).strip().replace(",", "."))

    def proxima_etapa(u):
        """Primeira etapa do onboarding que ainda falta (ou None se o perfil está completo)."""
        if not (u["apelido"] and u["data_nascimento"] and u["sexo_biologico"] and u["altura_cm"]
                and peso_atual(u["id"])):
            return "perfil_dados"
        if not (u["biotipo"] and u["objetivo"]):
            return "perfil_objetivo"
        return None

    # ---------- rotas ----------
    @app.route("/")
    def index():
        return redirect(url_for("perfil_resultado" if session.get("usuario_id") else "login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            ident = request.form.get("usuario", "").strip()
            senha = request.form.get("senha", "")
            if "@" in ident:
                u = get_db().execute("SELECT * FROM usuarios WHERE email = ?", (ident.lower(),)).fetchone()
            else:
                u = get_db().execute("SELECT * FROM usuarios WHERE cpf = ?", (re.sub(r"\D", "", ident),)).fetchone()
            if u is None or not check_password_hash(u["senha_hash"], senha):
                return render_template("login.html", erro="E-mail/CPF ou senha incorretos."), 401
            session.clear()
            session["usuario_id"] = u["id"]
            session.permanent = bool(request.form.get("lembrar"))
            return redirect(url_for(proxima_etapa(u) or "perfil_resultado"))
        return render_template("login.html")

    @app.route("/sair")
    def sair():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/cadastro", methods=["GET", "POST"])
    def cadastro():
        if request.method == "POST":
            f = request.form
            nome = f.get("nome", "").strip()
            cpf = re.sub(r"\D", "", f.get("cpf", ""))
            celular = re.sub(r"\D", "", f.get("celular", ""))
            email = f.get("email", "").strip().lower()
            senha, confirmar = f.get("senha", ""), f.get("confirmar", "")

            erro = None
            if len(nome) < 3:
                erro = "Informe seu nome completo."
            elif len(cpf) != 11:
                erro = "O CPF deve ter 11 números."
            elif len(celular) not in (10, 11):
                erro = "Informe o celular com DDD."
            elif "@" not in email:
                erro = "Informe um e-mail válido."
            elif len(senha) < 8:
                erro = "A senha precisa ter no mínimo 8 caracteres."
            elif senha != confirmar:
                erro = "As senhas não conferem."
            elif not f.get("termos"):
                erro = "É preciso aceitar os Termos de Uso e a Política de Privacidade."
            else:
                db = get_db()
                if db.execute("SELECT 1 FROM usuarios WHERE email = ? OR cpf = ?", (email, cpf)).fetchone():
                    erro = "Já existe uma conta com esse e-mail ou CPF."
            if erro:
                return render_template("cadastro.html", erro=erro), 400

            uid = str(uuid.uuid4())
            db.execute(
                "INSERT INTO usuarios (id, nome_completo, email, cpf, celular, senha_hash) VALUES (?,?,?,?,?,?)",
                (uid, nome, email, cpf, celular, generate_password_hash(senha)))
            db.commit()
            session.clear()
            session["usuario_id"] = uid
            return redirect(url_for("perfil_dados"))  # segue para o onboarding
        return render_template("cadastro.html")

    @app.route("/esqueci-senha", methods=["GET", "POST"])
    def esqueci_senha():
        if request.method == "POST":
            # TODO: gerar token e enviar e-mail. Resposta idêntica exista ou não a conta
            # (não revela quais e-mails estão cadastrados).
            return redirect(url_for("esqueci_senha") + "#enviado")
        return render_template("esqueci-senha.html")

    @app.route("/perfil/1-dados", methods=["GET", "POST"])
    @login_required
    def perfil_dados():
        if request.method == "POST":
            f = request.form
            try:
                apelido = f.get("apelido", "").strip()
                nasc = date.fromisoformat(f.get("nascimento", ""))
                sexo = f.get("sexo", "")
                peso = numero(f.get("peso"))
                altura = int(numero(f.get("altura")))
                peso_meta = numero(f["peso-meta"]) if f.get("peso-meta", "").strip() else None
            except (ValueError, KeyError):
                return render_template("perfil-1-dados.html", erro="Confira os dados informados."), 400

            erro = None
            if not 1 <= len(apelido) <= 20:
                erro = "O apelido deve ter entre 1 e 20 caracteres."
            elif not (date(1920, 1, 1) <= nasc and calculos.idade(nasc) >= 14):
                erro = "Data de nascimento inválida (idade mínima: 14 anos)."
            elif sexo not in SEXOS:
                erro = "Selecione o sexo biológico."
            elif not 30 <= peso <= 300 or not 100 <= altura <= 250:
                erro = "Peso ou altura fora do intervalo permitido."
            elif peso_meta is not None and not 30 <= peso_meta <= 300:
                erro = "Peso desejado fora do intervalo permitido."
            if erro:
                return render_template("perfil-1-dados.html", erro=erro), 400

            avatar_url = g.usuario["avatar_url"]
            foto = request.files.get("foto")
            if foto and foto.filename:
                ext = IMAGENS.get(foto.mimetype)
                if ext is None:
                    return render_template("perfil-1-dados.html", erro="A foto deve ser JPG, PNG, WEBP ou GIF."), 400
                nome_arq = f"{uuid.uuid4().hex}.{ext}"
                foto.save(Path(app.config["UPLOAD_DIR"]) / nome_arq)
                avatar_url = f"uploads/{nome_arq}"

            db = get_db()
            db.execute(
                "UPDATE usuarios SET apelido=?, data_nascimento=?, sexo_biologico=?, altura_cm=?, "
                "peso_meta_kg=?, avatar_url=? WHERE id=?",
                (apelido, nasc.isoformat(), sexo, altura, peso_meta, avatar_url, g.usuario["id"]))
            ultimo = peso_atual(g.usuario["id"])
            if ultimo is None or abs(ultimo - peso) > 1e-6:  # novo ponto no gráfico de evolução
                db.execute(
                    "INSERT INTO historico_medidas (id, usuario_id, peso_kg, objetivo_momento) VALUES (?,?,?,?)",
                    (str(uuid.uuid4()), g.usuario["id"], peso, g.usuario["objetivo"]))
            db.commit()
            return redirect(url_for("perfil_objetivo"))
        return render_template("perfil-1-dados.html")

    @app.route("/perfil/2-objetivo", methods=["GET", "POST"])
    @login_required
    def perfil_objetivo():
        if request.method == "POST":
            biotipo, objetivo = request.form.get("biotipo"), request.form.get("objetivo")
            if biotipo not in BIOTIPOS or objetivo not in OBJETIVOS:
                return render_template("perfil-2-objetivo.html", erro="Selecione o biotipo e o objetivo."), 400
            db = get_db()
            db.execute("UPDATE usuarios SET biotipo=?, objetivo=? WHERE id=?", (biotipo, objetivo, g.usuario["id"]))
            db.commit()
            return redirect(url_for("perfil_esportes"))
        return render_template("perfil-2-objetivo.html")

    @app.route("/perfil/3-esportes", methods=["GET", "POST"])
    @login_required
    def perfil_esportes():
        if request.method == "POST":
            linhas = []
            for esporte in request.form.getlist("esporte"):
                freq = request.form.get(f"freq-{esporte}")
                inte = request.form.get(f"int-{esporte}")
                if esporte not in ESPORTES or freq not in FREQUENCIAS or inte not in INTENSIDADES:
                    return render_template(
                        "perfil-3-esportes.html",
                        erro=f"Informe frequência e intensidade de {ESPORTES.get(esporte, esporte)}."), 400
                linhas.append((str(uuid.uuid4()), g.usuario["id"], esporte, freq, inte))
            db = get_db()
            db.execute("DELETE FROM esportes_usuario WHERE usuario_id = ?", (g.usuario["id"],))
            db.executemany(
                "INSERT INTO esportes_usuario (id, usuario_id, esporte, frequencia, intensidade) VALUES (?,?,?,?,?)",
                linhas)
            db.commit()
            return redirect(url_for("perfil_resultado"))
        return render_template("perfil-3-esportes.html")

    @app.route("/perfil/4-resultado")
    @login_required
    def perfil_resultado():
        u = g.usuario
        faltando = proxima_etapa(u)
        if faltando:
            return redirect(url_for(faltando))

        db = get_db()
        esportes = [dict(r) for r in db.execute(
            "SELECT esporte, frequencia, intensidade FROM esportes_usuario WHERE usuario_id = ? ORDER BY rowid",
            (u["id"],))]
        anos = calculos.idade(date.fromisoformat(u["data_nascimento"]))
        peso = peso_atual(u["id"])
        m = calculos.calcular_metas(u["sexo_biologico"], anos, peso, u["altura_cm"], u["objetivo"], esportes)

        # grava/atualiza as metas de hoje (metas_nutricionais)
        hoje = date.today().isoformat()
        db.execute("DELETE FROM metas_nutricionais WHERE usuario_id = ? AND data_inicio = ?", (u["id"], hoje))
        db.execute(
            "INSERT INTO metas_nutricionais (id, usuario_id, data_inicio, meta_agua_ml, meta_calorias, "
            "meta_proteina_g, meta_carbo_g, meta_gordura_g) VALUES (?,?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), u["id"], hoje, m["agua_ml"], m["meta"], m["prot_g"], m["carb_g"], m["gord_g"]))
        db.commit()

        perfil = {
            "sexo": SEXOS[u["sexo_biologico"]], "idade": anos, "peso": peso, "altura": u["altura_cm"],
            "biotipo": BIOTIPOS[u["biotipo"]], "objetivo": OBJETIVOS[u["objetivo"]],
            "esportes": [{
                "nome": ESPORTES[e["esporte"]], "frequencia": e["frequencia"], "intensidade": e["intensidade"],
                "resumo": f'{e["frequencia"]} {ESPORTES[e["esporte"]].lower()} {e["intensidade"]}',
            } for e in esportes],
        }
        aj = m["ajuste"]
        return render_template(
            "perfil-4-resultado.html", p=perfil, m=m,
            ajuste_sinal="−" if aj < 0 else "+" if aj > 0 else "",
            ajuste_texto="Déficit moderado e seguro" if aj < 0 else "Superávit moderado" if aj > 0 else "Manutenção do peso",
            ajuste_tag=f"🔥 Déficit de {abs(aj)} kcal" if aj < 0 else f"💪 Superávit de {aj} kcal" if aj > 0 else "Manutenção")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
