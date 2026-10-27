"""Metas diárias do passo 4 do perfil (fórmulas descritas em perfil-4-resultado.html)."""
from datetime import date

# kcal gastas por sessão, por intensidade (estimativa; calibrada no exemplo do mockup)
KCAL_SESSAO = {"leve": 200, "moderada": 350, "intensa": 450, "máxima": 550}
AJUSTE_OBJETIVO = {"emagrecimento": -500, "manutencao": 0, "saude": 0, "hipertrofia": 400}
FATOR_NEAT_TEF = 0.276  # atividade diária + efeito térmico, como fração do TMB (mockup: 487/1763)


def arredonda(x: float) -> int:
    """Meio para cima (1762,5 -> 1763), diferente do round() do Python (par mais próximo)."""
    return int(x + 0.5)


def idade(nascimento: date, hoje: date | None = None) -> int:
    hoje = hoje or date.today()
    return hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))


def vezes_por_semana(frequencia: str) -> int:
    return 7 if frequencia.strip().lower() == "diário" else int(frequencia.strip().rstrip("x"))


def calcular_metas(sexo, anos, peso_kg, altura_cm, objetivo, esportes):
    """esportes: lista de dicts com 'frequencia' e 'intensidade'."""
    tmb = 10 * peso_kg + 6.25 * altura_cm - 5 * anos + (5 if sexo == "masculino" else -161)
    gasto = sum(
        KCAL_SESSAO[e["intensidade"]] * vezes_por_semana(e["frequencia"]) / 7 for e in esportes
    )
    tmb_r, gasto_r, neat_r = arredonda(tmb), arredonda(gasto), arredonda(tmb * FATOR_NEAT_TEF)
    tdee = tmb_r + gasto_r + neat_r
    ajuste = AJUSTE_OBJETIVO[objetivo]
    meta = tdee + ajuste

    prot = arredonda(2.1 * peso_kg)
    gord = arredonda(0.8 * peso_kg)
    carb = max(0, arredonda((meta - prot * 4 - gord * 9) / 4))
    agua = arredonda(35 * peso_kg / 50) * 50

    return {
        "tmb": tmb_r, "gasto_esportes": gasto_r, "neat": neat_r, "tdee": tdee,
        "ajuste": ajuste, "meta": meta,
        "prot_g": prot, "carb_g": carb, "gord_g": gord, "agua_ml": agua,
        "prot_pct": arredonda(prot * 4 / meta * 100), "carb_pct": arredonda(carb * 4 / meta * 100),
        "gord_pct": arredonda(gord * 9 / meta * 100),
        # equivalências aproximadas ("na prática")
        "frango_g": round(prot / 0.31 / 10) * 10, "arroz_g": round(carb / 0.28 / 10) * 10,
        "azeite_colheres": arredonda(gord / 13), "copos": arredonda(agua / 250), "garrafas": int(agua / 500),
    }
