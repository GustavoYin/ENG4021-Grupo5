"""Teste do fluxo completo: cadastro -> perfil 1..4 -> login. Rode: python -m unittest -v"""
import io
import tempfile
import unittest
from pathlib import Path

from app import create_app


class FluxoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({"DATABASE": str(Path(self.tmp.name) / "t.db"),
                               "UPLOAD_DIR": self.tmp.name, "TESTING": True})
        self.c = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def cadastrar(self, **extra):
        dados = dict(nome="Edson Silva", cpf="123.456.789-09", celular="(21) 99999-9999",
                     email="Edson@Email.com", senha="senha1234", confirmar="senha1234", termos="on")
        dados.update(extra)
        return self.c.post("/cadastro", data=dados)

    def test_telas_publicas_renderizam(self):
        for url in ("/login", "/cadastro", "/esqueci-senha"):
            self.assertEqual(self.c.get(url).status_code, 200, url)
        self.assertEqual(self.c.get("/static/style.css").status_code, 200)

    def test_telas_privadas_exigem_login(self):
        for url in ("/perfil/1-dados", "/perfil/2-objetivo", "/perfil/3-esportes", "/perfil/4-resultado"):
            r = self.c.get(url)
            self.assertEqual((r.status_code, r.location), (302, "/login"), url)

    def test_cadastro_validacoes(self):
        self.assertIn("não conferem", self.cadastrar(confirmar="outra").get_data(as_text=True))
        self.assertEqual(self.cadastrar(cpf="123").status_code, 400)
        self.assertEqual(self.cadastrar().status_code, 302)
        self.assertIn("Já existe", self.cadastrar().get_data(as_text=True))

    def test_fluxo_completo_e_metas(self):
        self.assertEqual(self.cadastrar().location, "/perfil/1-dados")
        r = self.c.post("/perfil/1-dados", content_type="multipart/form-data", data={
            "apelido": "Edson", "nascimento": "1998-01-01", "sexo": "masculino",
            "peso": "78,5", "altura": "178", "peso-meta": "74",
            "foto": (io.BytesIO(b"\x89PNG"), "foto.png", "image/png")})
        self.assertEqual(r.location, "/perfil/2-objetivo")
        r = self.c.post("/perfil/2-objetivo", data={"biotipo": "mesomorfo", "objetivo": "emagrecimento"})
        self.assertEqual(r.location, "/perfil/3-esportes")
        r = self.c.post("/perfil/3-esportes", data={
            "esporte": ["musculacao", "corrida"],
            "freq-musculacao": "5x", "int-musculacao": "intensa",
            "freq-corrida": "2x", "int-corrida": "moderada"})
        self.assertEqual(r.location, "/perfil/4-resultado")

        html = self.c.get("/perfil/4-resultado").get_data(as_text=True)
        # valores determinísticos do mockup (TMB, proteína, gordura, água)
        for esperado in ("1.763 kcal", "Mesomorfo", "78,5 kg", "Musculação 5x", "165 g", "63 g", "2.750 ml"):
            self.assertIn(esperado, html)

        with self.app.app_context():
            from database import get_db
            meta = get_db().execute("SELECT * FROM metas_nutricionais").fetchone()
            self.assertGreater(meta["meta_calorias"], 2000)
            kcal = meta["meta_proteina_g"] * 4 + meta["meta_carbo_g"] * 4 + meta["meta_gordura_g"] * 9
            self.assertAlmostEqual(kcal, meta["meta_calorias"], delta=4)  # macros fecham com a meta
            self.assertEqual(get_db().execute("SELECT COUNT(*) FROM historico_medidas").fetchone()[0], 1)

    def test_calculos_mockup(self):
        import calculos
        m = calculos.calcular_metas("masculino", 28, 78.5, 178, "emagrecimento", [])
        self.assertEqual((m["tmb"], m["prot_g"], m["gord_g"], m["agua_ml"]), (1763, 165, 63, 2750))
        self.assertEqual(calculos.vezes_por_semana("Diário"), 7)

    def test_login_logout_e_senha_errada(self):
        self.cadastrar()
        self.c.get("/sair")
        self.assertEqual(self.c.post("/login", data={"usuario": "edson@email.com", "senha": "errada123"}).status_code, 401)
        r = self.c.post("/login", data={"usuario": "12345678909", "senha": "senha1234"})  # login por CPF
        self.assertEqual((r.status_code, r.location), (302, "/perfil/1-dados"))

    def test_esqueci_senha_nao_revela_cadastro(self):
        r = self.c.post("/esqueci-senha", data={"email": "naoexiste@x.com"})
        self.assertEqual(r.location, "/esqueci-senha#enviado")


if __name__ == "__main__":
    unittest.main()
