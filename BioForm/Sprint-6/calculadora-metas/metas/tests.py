from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from saude.models import Esporte, EsporteUsuario, HistoricoMedida, MetaNutricional, Usuario

from .calculo import calcular_metas, salvar_meta


def criar_usuario(nome, cpf):
    return Usuario.objects.create(
        nome_completo=nome,
        cpf=cpf,
        celular='21999990000',
        data_nascimento=date(2000, 1, 1),
        sexo_biologico='feminino',
        altura_cm=165,
        biotipo='mesomorfo',
    )


class CalculadoraDeMetasTest(TestCase):
    def test_exemplo_do_mockup(self):
        # masculino, 28 anos, 78,5 kg, 178 cm, perder peso, musculação 5x intensa + corrida 2x moderada
        metas = calcular_metas('masculino', 28, Decimal('78.5'), 178, 'emagrecimento',
                               [(Decimal('5.0'), 5, 'intensa'), (Decimal('8.0'), 2, 'moderada')])
        self.assertEqual(metas.tmb, 1763)
        self.assertEqual(metas.gasto_esportes, 437)
        self.assertEqual(metas.ajuste, -500)
        self.assertEqual(metas.calorias, metas.tdee - 500)
        self.assertEqual(metas.proteina_g, 165)  # 2,1 g/kg
        self.assertEqual(metas.gordura_g, 63)  # 0,8 g/kg
        self.assertEqual(metas.agua_ml, 2750)  # 35 ml/kg
        self.assertEqual(metas.carbo_g, round((metas.calorias - 165 * 4 - 63 * 9) / 4))

    def test_tmb_feminina(self):
        metas = calcular_metas('feminino', 30, 60, 165, 'manutencao')
        self.assertEqual(metas.tmb, 1320)  # 600 + 1031,25 - 150 - 161
        self.assertEqual(metas.gasto_esportes, 0)
        self.assertEqual(metas.ajuste, 0)

    def test_hipertrofia_tem_superavit(self):
        metas = calcular_metas('masculino', 25, 70, 175, 'hipertrofia')
        self.assertEqual(metas.ajuste, 400)
        self.assertEqual(metas.proteina_g, 140)  # 2,0 g/kg

    def test_meta_nunca_fica_abaixo_da_tmb(self):
        metas = calcular_metas('feminino', 60, 50, 150, 'emagrecimento')
        self.assertTrue(metas.piso_tmb)
        self.assertEqual(metas.calorias, metas.tmb)
        self.assertGreater(metas.ajuste, -500)

    def test_intensidade_aumenta_o_gasto(self):
        leve = calcular_metas('masculino', 30, 80, 180, 'manutencao', [(8, 3, 'leve')])
        maxima = calcular_metas('masculino', 30, 80, 180, 'manutencao', [(8, 3, 'maxima')])
        self.assertGreater(maxima.gasto_esportes, leve.gasto_esportes)

    def test_salvar_meta_cria_uma_por_dia(self):
        ana = criar_usuario('Ana', '12345678901')
        HistoricoMedida.objects.create(usuario=ana, data_registro=timezone.now(), peso_kg=Decimal('60'),
                                       objetivo_momento='manutencao')
        meta, metas = salvar_meta(ana)
        self.assertEqual(meta.meta_calorias, metas.calorias)
        self.assertEqual(meta.meta_agua_ml, 2100)
        EsporteUsuario.objects.create(usuario=ana, esporte=Esporte.objects.get(nome='Corrida'),
                                      frequencia_semanal=3, intensidade='moderada')
        meta_nova, _ = salvar_meta(ana)
        self.assertEqual(MetaNutricional.objects.filter(usuario=ana).count(), 1)
        self.assertGreater(meta_nova.meta_calorias, metas.calorias)
