from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from .models import (
    Alimento,
    Amizade,
    Desafio,
    DiarioConsumo,
    Esporte,
    EsporteUsuario,
    Grupo,
    MedidaCaseira,
    MembroGrupo,
    PerfilGamificacao,
    RegistroRefeicao,
    RegistroRefeicaoItem,
    RegistroXP,
    Usuario,
)


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


class CatalogosTest(TestCase):
    def test_catalogo_de_alimentos_populado_com_taco(self):
        self.assertEqual(Alimento.objects.count(), 591)

    def test_macros_do_peito_de_frango_grelhado(self):
        frango = Alimento.objects.get(nome='Frango, peito, sem pele, grelhado')
        self.assertEqual(frango.porcao_padrao, '100g')
        self.assertEqual(frango.porcao_gramas, Decimal('100'))
        self.assertEqual(frango.kcal, Decimal('159'))
        self.assertEqual(frango.proteina_g, Decimal('32.0'))
        self.assertEqual(frango.gordura_g, Decimal('2.5'))

    def test_catalogo_de_esportes_populado(self):
        self.assertEqual(Esporte.objects.count(), 10)
        self.assertTrue(Esporte.objects.filter(nome='Futevôlei').exists())


class PerfilTest(TestCase):
    def test_cpf_precisa_ter_11_numeros(self):
        usuario = criar_usuario('Ana', '12345678901')
        usuario.cpf = '123.456.789-01'
        with self.assertRaises(ValidationError):
            usuario.full_clean()

    def test_esporte_nao_repete_no_perfil(self):
        ana = criar_usuario('Ana', '12345678901')
        corrida = Esporte.objects.get(nome='Corrida')
        EsporteUsuario.objects.create(usuario=ana, esporte=corrida, frequencia_semanal=2, intensidade='moderada')
        with self.assertRaises(IntegrityError), transaction.atomic():
            EsporteUsuario.objects.create(usuario=ana, esporte=corrida, frequencia_semanal=3, intensidade='leve')


class DiarioAlimentarTest(TestCase):
    def setUp(self):
        self.ana = criar_usuario('Ana', '12345678901')
        self.diario = DiarioConsumo.objects.create(usuario=self.ana, data_referencia=date(2026, 10, 8))

    def test_um_diario_por_usuario_por_dia(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            DiarioConsumo.objects.create(usuario=self.ana, data_referencia=date(2026, 10, 8))

    def test_macros_de_um_alimento_em_medida_caseira(self):
        arroz = Alimento.objects.get(nome='Arroz, tipo 1, cozido')  # 128 kcal / 28,1 g carbo por 100 g
        colher = MedidaCaseira.objects.create(alimento=arroz, nome='1 colher de servir', gramas=Decimal('50'))
        almoco = RegistroRefeicao.objects.create(diario=self.diario, tipo_refeicao='almoco', horario=timezone.now())
        item = RegistroRefeicaoItem.objects.create(
            registro=almoco, alimento=arroz, medida_caseira=colher, quantidade=Decimal('3'),
        )
        self.assertEqual(item.gramas(), Decimal('150'))
        self.assertEqual(item.macros()['kcal'], Decimal('192'))
        self.assertEqual(item.macros()['carbo_g'], Decimal('42.15'))

    def test_macros_em_porcoes_padrao(self):
        frango = Alimento.objects.get(nome='Frango, peito, sem pele, grelhado')
        jantar = RegistroRefeicao.objects.create(diario=self.diario, tipo_refeicao='jantar', horario=timezone.now())
        item = RegistroRefeicaoItem.objects.create(registro=jantar, alimento=frango, quantidade=Decimal('1.5'))
        self.assertEqual(item.gramas(), Decimal('150'))
        self.assertEqual(item.macros()['proteina_g'], Decimal('48'))


class GamificacaoTest(TestCase):
    def setUp(self):
        self.ana = criar_usuario('Ana', '12345678901')
        self.bruno = criar_usuario('Bruno', '10987654321')
        self.carla = criar_usuario('Carla', '11122233344')

    def test_amizade_nao_repete(self):
        Amizade.objects.create(usuario_1=self.ana, usuario_2=self.bruno)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Amizade.objects.create(usuario_1=self.ana, usuario_2=self.bruno)

    def test_usuario_nao_e_amigo_de_si_mesmo(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Amizade.objects.create(usuario_1=self.ana, usuario_2=self.ana)

    def test_nivel_segue_os_patamares(self):
        perfil = PerfilGamificacao.objects.create(usuario=self.ana, pontos_experiencia=499)
        self.assertEqual(perfil.nivel()['nome'], 'Iniciante')
        perfil.pontos_experiencia = 1500
        self.assertEqual(perfil.nivel()['selo'], 'Prata')
        perfil.pontos_experiencia = 10000
        self.assertEqual(perfil.nivel()['nome'], 'Lenda')

    def test_ranking_semanal_do_grupo(self):
        grupo = Grupo.objects.create(nome='Galera', criador=self.ana, codigo_convite='ABC123')
        for usuario in (self.ana, self.bruno, self.carla):
            MembroGrupo.objects.create(grupo=grupo, usuario=usuario)
        quinta = date(2026, 10, 8)
        RegistroXP.objects.create(usuario=self.ana, acao='treino', pontos=50, data_referencia=quinta)
        RegistroXP.objects.create(usuario=self.bruno, acao='treino', pontos=50, data_referencia=quinta)
        RegistroXP.objects.create(usuario=self.bruno, acao='dieta_perfeita', pontos=40, data_referencia=date(2026, 10, 5))
        # semana anterior: não conta (o ranking zera no domingo)
        RegistroXP.objects.create(usuario=self.carla, acao='treino', pontos=500, data_referencia=date(2026, 10, 4))

        ranking = list(grupo.ranking_semanal(quinta))
        self.assertEqual([u.nome_completo for u in ranking], ['Bruno', 'Ana', 'Carla'])
        self.assertEqual([u.xp_semana for u in ranking], [90, 50, 0])

    def test_desafio_nao_termina_antes_de_comecar(self):
        grupo = Grupo.objects.create(nome='Galera', criador=self.ana, codigo_convite='XYZ789')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Desafio.objects.create(
                grupo=grupo, criador=self.ana, nome='Outubro', metrica='xp',
                data_inicio=date(2026, 10, 31), data_fim=date(2026, 10, 1),
            )
