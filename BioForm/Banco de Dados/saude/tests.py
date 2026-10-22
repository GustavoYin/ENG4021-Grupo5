import importlib
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import cpf_valido
from .metas import calcular_metas, metas_do_usuario, salvar_meta
from .models import (
    Alimento,
    Amizade,
    Desafio,
    DiarioConsumo,
    Esporte,
    EsporteUsuario,
    Grupo,
    HistoricoMedida,
    MedidaCaseira,
    MembroGrupo,
    MetaNutricional,
    PerfilGamificacao,
    RegistroRefeicao,
    RegistroRefeicaoItem,
    RegistroXP,
    Usuario,
)

User = get_user_model()


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


# =====================================================================
# Sprint 6 - medidas caseiras, calculadora de metas e telas de conta
# =====================================================================

CPF_ANA = '52998224725'  # CPFs de teste com dígitos verificadores válidos
CPF_BRUNO = '11144477735'
SENHA = 'treino-forte-2026'


class MedidasCaseirasTest(TestCase):
    def test_todas_as_medidas_da_migracao_foram_carregadas(self):
        migracao = importlib.import_module('saude.migrations.0004_popular_medidas_caseiras')
        esperado = sum(len(medidas) for _, medidas in migracao.MEDIDAS.values())
        self.assertEqual(MedidaCaseira.objects.count(), esperado)

    def test_pao_frances_e_concha_de_feijao(self):
        pao = MedidaCaseira.objects.get(alimento__nome='Pão, trigo, francês', nome='1 unidade')
        self.assertEqual(pao.gramas, Decimal('50'))
        concha = MedidaCaseira.objects.get(alimento__nome='Feijão, carioca, cozido', nome='1 concha média')
        self.assertEqual(concha.gramas, Decimal('140'))

    def test_registrar_refeicao_com_medida_carregada(self):
        ana = criar_usuario('Ana', '12345678901')
        diario = DiarioConsumo.objects.create(usuario=ana, data_referencia=date(2026, 10, 22))
        almoco = RegistroRefeicao.objects.create(diario=diario, tipo_refeicao='almoco', horario=timezone.now())
        colher = MedidaCaseira.objects.get(alimento__nome='Azeite, de oliva, extra virgem', nome='1 colher de sopa')
        item = RegistroRefeicaoItem.objects.create(
            registro=almoco, alimento=colher.alimento, medida_caseira=colher, quantidade=Decimal('2'),
        )
        self.assertEqual(item.gramas(), Decimal('26'))
        self.assertEqual(item.macros()['gordura_g'], Decimal('26'))
        self.assertEqual(item.macros()['kcal'], Decimal('229.84'))


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


def dados_cadastro(**extra):
    dados = {
        'nome_completo': 'Ana Souza', 'cpf': '529.982.247-25', 'celular': '(21) 99999-0000',
        'email': 'Ana@Email.com', 'senha': SENHA, 'confirmar': SENHA, 'aceitou_termos': 'on',
    }
    dados.update(extra)
    return dados


class CadastroELoginTest(TestCase):
    def test_validacao_do_cpf(self):
        self.assertTrue(cpf_valido(CPF_ANA))
        self.assertTrue(cpf_valido(CPF_BRUNO))
        self.assertFalse(cpf_valido('52998224724'))
        self.assertFalse(cpf_valido('11111111111'))

    def test_cadastro_cria_conta_e_perfil_e_entra(self):
        resposta = self.client.post(reverse('cadastro'), dados_cadastro())
        self.assertRedirects(resposta, reverse('perfil_dados'))
        conta = User.objects.get(email='ana@email.com')
        self.assertTrue(conta.check_password(SENHA))
        self.assertEqual(conta.usuario.cpf, CPF_ANA)
        self.assertEqual(conta.usuario.celular, '21999990000')
        self.assertTrue(conta.usuario.aceitou_termos)
        self.assertEqual(int(self.client.session['_auth_user_id']), conta.pk)

    def test_cadastro_repete_a_validacao_no_servidor(self):
        casos = {
            'cpf': dados_cadastro(cpf='529.982.247-24'),
            'confirmar': dados_cadastro(confirmar='outra-senha-2026'),
            'senha': dados_cadastro(senha='12345678', confirmar='12345678'),
            'aceitou_termos': dados_cadastro(aceitou_termos=''),
            'celular': dados_cadastro(celular='9999'),
        }
        for campo, dados in casos.items():
            with self.subTest(campo=campo):
                resposta = self.client.post(reverse('cadastro'), dados)
                self.assertEqual(resposta.status_code, 200)
                self.assertIn(campo, resposta.context['form'].errors)
        self.assertFalse(User.objects.exists())

    def test_cpf_e_email_nao_repetem(self):
        self.client.post(reverse('cadastro'), dados_cadastro())
        self.client.post(reverse('sair'))
        resposta = self.client.post(reverse('cadastro'), dados_cadastro(email='ANA@email.com', cpf=CPF_BRUNO))
        self.assertIn('email', resposta.context['form'].errors)
        resposta = self.client.post(reverse('cadastro'), dados_cadastro(email='outra@email.com'))
        self.assertIn('cpf', resposta.context['form'].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_entrar_com_email_ou_cpf(self):
        self.client.post(reverse('cadastro'), dados_cadastro())
        for identificador in ('ana@email.com', 'ANA@EMAIL.COM', CPF_ANA, '529.982.247-25'):
            with self.subTest(identificador=identificador):
                self.client.post(reverse('sair'))
                resposta = self.client.post(reverse('entrar'), {'username': identificador, 'password': SENHA})
                self.assertRedirects(resposta, reverse('inicio'), fetch_redirect_response=False)

    def test_senha_errada_nao_entra(self):
        self.client.post(reverse('cadastro'), dados_cadastro())
        self.client.post(reverse('sair'))
        resposta = self.client.post(reverse('entrar'), {'username': CPF_ANA, 'password': 'errada-123'})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'E-mail/CPF ou senha incorretos.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_lembrar_de_mim(self):
        self.client.post(reverse('cadastro'), dados_cadastro())
        self.client.post(reverse('sair'))
        self.client.post(reverse('entrar'), {'username': CPF_ANA, 'password': SENHA})
        self.assertTrue(self.client.session.get_expire_at_browser_close())
        self.client.post(reverse('sair'))
        self.client.post(reverse('entrar'), {'username': CPF_ANA, 'password': SENHA, 'lembrar': 'on'})
        self.assertFalse(self.client.session.get_expire_at_browser_close())

    def test_paginas_do_perfil_exigem_login(self):
        for nome in ('perfil_dados', 'perfil_metas', 'conta', 'usuarios'):
            with self.subTest(pagina=nome):
                resposta = self.client.get(reverse(nome))
                self.assertEqual(resposta.status_code, 302)
                self.assertTrue(resposta.url.startswith(reverse('entrar')))

    def test_esqueci_minha_senha_envia_link(self):
        self.client.post(reverse('cadastro'), dados_cadastro())
        self.client.post(reverse('sair'))
        resposta = self.client.post(reverse('senha_esqueci'), {'email': 'ana@email.com'})
        self.assertRedirects(resposta, reverse('senha_enviada'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('/senha/nova/', mail.outbox[0].body)

    def test_pagina_404_personalizada(self):
        resposta = self.client.get('/pagina-que-nao-existe/')
        self.assertContains(resposta, 'Página não encontrada', status_code=404)


class OnboardingTest(TestCase):
    def setUp(self):
        self.client.post(reverse('cadastro'), dados_cadastro())
        self.usuario = Usuario.objects.get(cpf=CPF_ANA)

    def preencher_dados(self, peso='78.5'):
        return self.client.post(reverse('perfil_dados'), {
            'apelido': 'Aninha', 'data_nascimento': '1998-01-15', 'sexo_biologico': 'feminino',
            'peso_kg': peso, 'altura_cm': '168', 'peso_meta_kg': '',
        })

    def onboarding_completo(self):
        self.preencher_dados()
        self.client.post(reverse('perfil_objetivo'), {'biotipo': 'mesomorfo', 'objetivo': 'emagrecimento'})
        return self.client.post(reverse('perfil_esportes'), {
            'pratica_musculacao': 'on', 'freq_musculacao': '5', 'int_musculacao': 'intensa',
            'pratica_corrida': 'on', 'freq_corrida': '2', 'int_corrida': 'moderada',
            'freq_ciclismo': '3', 'int_ciclismo': 'moderada',  # não marcado: deve ser ignorado
        })

    def test_nao_pula_passos(self):
        self.assertRedirects(self.client.get(reverse('perfil_esportes')), reverse('perfil_dados'))
        self.assertRedirects(self.client.get(reverse('perfil_metas')), reverse('perfil_dados'))
        self.preencher_dados()
        self.assertRedirects(self.client.get(reverse('perfil_metas')), reverse('perfil_objetivo'))

    def test_passo_a_passo_ate_as_metas(self):
        self.assertRedirects(self.preencher_dados(), reverse('perfil_objetivo'))
        self.assertFalse(HistoricoMedida.objects.exists())  # o peso espera o objetivo do passo 2
        resposta = self.client.post(reverse('perfil_objetivo'), {'biotipo': 'mesomorfo', 'objetivo': 'emagrecimento'})
        self.assertRedirects(resposta, reverse('perfil_esportes'))
        self.assertRedirects(self.onboarding_completo(), reverse('perfil_metas'))

        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.apelido, 'Aninha')
        self.assertEqual(self.usuario.biotipo, 'mesomorfo')
        medida = self.usuario.medida_atual()
        self.assertEqual(medida.peso_kg, Decimal('78.5'))
        self.assertEqual(medida.objetivo_momento, 'emagrecimento')
        self.assertEqual(sorted(e.esporte.nome for e in self.usuario.esportes.all()), ['Corrida', 'Musculação'])

        metas = metas_do_usuario(self.usuario)
        meta = self.usuario.meta_atual()
        self.assertEqual(meta.meta_calorias, metas.calorias)
        self.assertEqual(meta.meta_proteina_g, Decimal(metas.proteina_g))

        pagina = self.client.get(reverse('perfil_metas'))
        self.assertContains(pagina, 'Suas metas estão prontas!')
        self.assertContains(pagina, 'Passo <b>4</b> de 4')
        self.assertEqual(pagina.context['metas'], metas)

    def test_esporte_marcado_sem_intensidade_da_erro(self):
        self.preencher_dados()
        self.client.post(reverse('perfil_objetivo'), {'biotipo': 'mesomorfo', 'objetivo': 'saude'})
        resposta = self.client.post(reverse('perfil_esportes'), {'pratica_natacao': 'on', 'freq_natacao': '2'})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Escolha a frequência e a intensidade de Natação.')

    def test_editar_peso_depois_recalcula_a_meta(self):
        self.onboarding_completo()
        self.client.get(reverse('perfil_concluir'))
        antes = self.usuario.meta_atual().meta_calorias
        resposta = self.preencher_dados(peso='85')
        self.assertRedirects(resposta, reverse('perfil_metas'))
        self.assertGreater(self.usuario.meta_atual().meta_calorias, antes)
        self.assertEqual(MetaNutricional.objects.filter(usuario=self.usuario).count(), 1)
        self.assertEqual(HistoricoMedida.objects.filter(usuario=self.usuario).count(), 1)  # mesmo dia: corrige
        self.assertEqual(self.usuario.medida_atual().peso_kg, Decimal('85'))

    def test_novo_peso_em_outro_dia_vira_novo_ponto_do_grafico(self):
        self.onboarding_completo()
        self.client.get(reverse('perfil_concluir'))
        HistoricoMedida.objects.update(data_registro=timezone.now() - timedelta(days=7))
        self.preencher_dados(peso='77')
        self.assertEqual(
            list(HistoricoMedida.objects.filter(usuario=self.usuario).values_list('peso_kg', flat=True)),
            [Decimal('77'), Decimal('78.5')],
        )


class ContaEUsuariosTest(TestCase):
    def setUp(self):
        self.client.post(reverse('cadastro'), dados_cadastro())
        self.conta = User.objects.get(email='ana@email.com')

    def test_editar_dados_da_conta(self):
        resposta = self.client.post(reverse('conta'), {
            'nome_completo': 'Ana Souza Lima', 'apelido': 'Aninha', 'email': 'nova@email.com', 'celular': '21988887777',
        })
        self.assertRedirects(resposta, reverse('conta'))
        self.conta.refresh_from_db()
        self.assertEqual(self.conta.email, 'nova@email.com')
        self.assertEqual(self.conta.usuario.nome_completo, 'Ana Souza Lima')
        self.client.post(reverse('sair'))
        resposta = self.client.post(reverse('entrar'), {'username': 'nova@email.com', 'password': SENHA})
        self.assertEqual(resposta.status_code, 302)

    def test_email_de_outra_conta_nao_pode(self):
        User.objects.create_user(username='bruno@email.com', email='bruno@email.com', password=SENHA)
        resposta = self.client.post(reverse('conta'), {
            'nome_completo': 'Ana Souza', 'apelido': '', 'email': 'Bruno@email.com', 'celular': '21999990000',
        })
        self.assertIn('email', resposta.context['form'].errors)

    def test_excluir_conta_pede_a_senha(self):
        resposta = self.client.post(reverse('excluir_conta'), {'senha': 'errada'})
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(User.objects.filter(pk=self.conta.pk).exists())
        resposta = self.client.post(reverse('excluir_conta'), {'senha': SENHA})
        self.assertRedirects(resposta, reverse('entrar'))
        self.assertFalse(User.objects.filter(pk=self.conta.pk).exists())
        self.assertFalse(Usuario.objects.filter(cpf=CPF_ANA).exists())

    def test_listagem_de_usuarios_so_para_a_equipe(self):
        resposta = self.client.get(reverse('usuarios'))
        self.assertEqual(resposta.status_code, 302)

        self.conta.is_staff = True
        self.conta.save()
        criar_usuario('Bruno Lima', CPF_BRUNO)
        resposta = self.client.get(reverse('usuarios'))
        self.assertContains(resposta, 'Ana Souza')
        self.assertContains(resposta, 'Bruno Lima')
        self.assertContains(resposta, '529.***.***-25')  # CPF mascarado

        resposta = self.client.get(reverse('usuarios'), {'q': '111.444'})
        self.assertEqual([u.nome_completo for u in resposta.context['pagina']], ['Bruno Lima'])
        resposta = self.client.get(reverse('usuarios'), {'status': 'completo'})
        self.assertEqual(len(resposta.context['pagina']), 0)

    def test_sair(self):
        resposta = self.client.post(reverse('sair'))
        self.assertRedirects(resposta, reverse('entrar'))
        self.assertNotIn('_auth_user_id', self.client.session)
