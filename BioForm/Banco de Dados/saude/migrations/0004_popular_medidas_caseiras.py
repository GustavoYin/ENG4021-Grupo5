"""
Popula as medidas caseiras (RF10 - registro por porções) dos alimentos mais
comuns no dia a dia: colher, concha, escumadeira, fatia, unidade, copo...

Os gramas são valores APROXIMADOS de referência para uma porção média, no
estilo das tabelas de medidas caseiras usadas em nutrição (ex.: Pinheiro et al.,
"Tabela para Avaliação de Consumo Alimentar em Medidas Caseiras"). Servem para
estimar o consumo; o grupo pode corrigir ou acrescentar medidas pelo admin.

Os alimentos são encontrados pelo código TACO (mesmo UUID fixo da migração 0002),
e cada medida também tem UUID fixo: rodar de novo não duplica nada.
"""
import uuid
from decimal import Decimal

from django.db import migrations

# Mesmo namespace da 0002_popular_alimentos_taco (UUID do alimento = código TACO)
NAMESPACE_TACO = uuid.UUID('6f1d1c3a-6a8e-4c55-9a39-0d9b6e2f7a10')
NAMESPACE_MEDIDAS = uuid.UUID('3c9e2b7d-1f4a-4d8e-9b6c-7a5e0f2d8c41')

# código TACO: (nome do alimento, só para leitura) -> [(medida, gramas), ...]
MEDIDAS = {
    # ----- Cereais, pães e massas -----
    1: ('Arroz, integral, cozido', [('1 colher de sopa cheia', '25'), ('1 colher de servir', '45'), ('1 escumadeira', '90')]),
    3: ('Arroz, tipo 1, cozido', [('1 colher de sopa cheia', '25'), ('1 colher de servir', '45'), ('1 escumadeira', '90')]),
    7: ('Aveia, flocos, crua', [('1 colher de sopa', '15'), ('1/2 xícara', '40')]),
    8: ('Biscoito, doce, maisena', [('1 unidade', '5')]),
    13: ('Biscoito, salgado, cream cracker', [('1 unidade', '6')]),
    52: ('Pão, trigo, forma, integral', [('1 fatia', '25')]),
    53: ('Pão, trigo, francês', [('1 unidade', '50')]),
    61: ('Pipoca, com óleo de soja, sem sal', [('1 xícara', '8')]),
    533: ('Cuscuz, de milho, cozido com sal', [('1 pedaço médio', '100')]),
    542: ('Macarrão, molho bolognesa', [('1 pegador', '110')]),
    551: ('Tapioca, com manteiga', [('1 unidade média', '70')]),

    # ----- Leguminosas -----
    561: ('Feijão, carioca, cozido', [('1 colher de sopa', '17'), ('1 concha pequena', '80'), ('1 concha média', '140')]),
    567: ('Feijão, preto, cozido', [('1 colher de sopa', '17'), ('1 concha pequena', '80'), ('1 concha média', '140')]),
    577: ('Lentilha, cozida', [('1 colher de sopa', '20'), ('1 concha média', '100')]),
    540: ('Feijoada', [('1 concha média', '150')]),

    # ----- Carnes, ovos e peixes -----
    410: ('Frango, peito, sem pele, grelhado', [('1 filé pequeno', '70'), ('1 filé médio', '100'), ('1 filé grande', '140')]),
    398: ('Frango, coxa, sem pele, cozida', [('1 coxa média (sem osso)', '60')]),
    377: ('Carne, bovina, patinho, sem gordura, grelhado', [('1 bife pequeno', '70'), ('1 bife médio', '100')]),
    346: ('Carne, bovina, contra-filé, sem gordura, grelhado', [('1 bife médio', '100')]),
    326: ('Carne, bovina, acém, moído, cozido', [('1 colher de sopa cheia', '25'), ('1 colher de servir', '50')]),
    488: ('Ovo, de galinha, inteiro, cozido/10minutos', [('1 unidade', '50')]),
    490: ('Ovo, de galinha, inteiro, frito', [('1 unidade', '50')]),
    439: ('Presunto, sem capa de gordura', [('1 fatia', '15')]),
    277: ('Atum, conserva em óleo', [('1 colher de sopa', '20'), ('1 lata (drenada)', '120')]),
    319: ('Sardinha, conserva em óleo', [('1 unidade', '30'), ('1 lata (drenada)', '85')]),
    308: ('Pescada, filé, frito', [('1 filé médio', '100')]),

    # ----- Leite e derivados -----
    448: ('Iogurte, natural', [('1 colher de sopa', '20'), ('1 pote', '170')]),
    459: ('Leite, de vaca, integral, pó', [('1 colher de sopa', '15')]),
    456: ('Leite, de vaca, desnatado, pó', [('1 colher de sopa', '15')]),
    461: ('Queijo, minas, frescal', [('1 fatia média', '30')]),
    467: ('Queijo, prato', [('1 fatia', '15')]),
    464: ('Queijo, parmesão', [('1 colher de sopa (ralado)', '5')]),
    468: ('Queijo, requeijão, cremoso', [('1 colher de sopa', '20')]),

    # ----- Frutas -----
    163: ('Abacate, cru', [('1 colher de sopa', '30')]),
    164: ('Abacaxi, cru', [('1 fatia média', '75')]),
    179: ('Banana, nanica, crua', [('1 unidade média', '85')]),
    182: ('Banana, prata, crua', [('1 unidade média', '60')]),
    200: ('Goiaba, vermelha, com casca, crua', [('1 unidade média', '170')]),
    214: ('Laranja, pêra, crua', [('1 unidade média', '130')]),
    215: ('Laranja, pêra, suco', [('1 copo americano (190 ml)', '190'), ('1 copo grande (250 ml)', '250')]),
    222: ('Maçã, Fuji, com casca, crua', [('1 unidade média', '130')]),
    225: ('Mamão, Formosa, cru', [('1 fatia média', '170')]),
    226: ('Mamão, Papaia, cru', [('1/2 unidade', '155')]),
    235: ('Melancia, crua', [('1 fatia média', '200')]),
    239: ('Morango, cru', [('1 unidade', '12')]),
    256: ('Uva, Itália, crua', [('10 bagos', '80')]),

    # ----- Verduras, legumes e tubérculos -----
    78: ('Alface, crespa, crua', [('1 folha média', '10')]),
    88: ('Batata, doce, cozida', [('1 pedaço médio', '70'), ('1 unidade média', '150')]),
    91: ('Batata, inglesa, cozida', [('1 colher de servir', '60'), ('1 unidade média', '140')]),
    100: ('Brócolis, cozido', [('1 colher de servir', '30')]),
    109: ('Cenoura, cozida', [('1 colher de sopa', '20')]),
    110: ('Cenoura, crua', [('1 colher de sopa (ralada)', '12'), ('1 unidade média', '110')]),
    116: ('Couve, manteiga, refogada', [('1 colher de sopa', '20')]),
    122: ('Farinha, de mandioca, torrada', [('1 colher de sopa', '16')]),
    129: ('Mandioca, cozida', [('1 pedaço médio', '70')]),
    131: ('Mandioca, farofa, temperada', [('1 colher de sopa', '15')]),
    157: ('Tomate, com semente, cru', [('1 fatia', '15'), ('1 unidade média', '100')]),

    # ----- Gorduras, açúcares e outros -----
    260: ('Azeite, de oliva, extra virgem', [('1 colher de chá', '4'), ('1 colher de sopa', '13')]),
    261: ('Manteiga, com sal', [('1 ponta de faca', '5'), ('1 colher de sopa', '15')]),
    263: ('Margarina, com óleo hidrogenado, com sal (65% de lipídeos)', [('1 ponta de faca', '5'), ('1 colher de sopa', '15')]),
    492: ('Açúcar, cristal', [('1 colher de chá', '5'), ('1 colher de sopa', '15')]),
    494: ('Açúcar, refinado', [('1 colher de chá', '5'), ('1 colher de sopa', '15')]),
    507: ('Mel, de abelha', [('1 colher de chá', '7'), ('1 colher de sopa', '20')]),
    491: ('Achocolatado, pó', [('1 colher de sopa', '12')]),
    471: ('Café, infusão 10%', [('1 xícara pequena (50 ml)', '50')]),
    558: ('Amendoim, torrado, salgado', [('1 colher de sopa', '15')]),
    588: ('Castanha-de-caju, torrada, salgada', [('1 punhado (10 unidades)', '25')]),
    589: ('Castanha-do-Brasil, crua', [('1 unidade', '4')]),
    594: ('Linhaça, semente', [('1 colher de sopa', '10')]),
}


def id_do_alimento(taco_id):
    return uuid.uuid5(NAMESPACE_TACO, 'taco-%s' % taco_id)


def id_da_medida(taco_id, nome):
    return uuid.uuid5(NAMESPACE_MEDIDAS, '%s-%s' % (taco_id, nome))


def popular(apps, schema_editor):
    Alimento = apps.get_model('saude', 'Alimento')
    MedidaCaseira = apps.get_model('saude', 'MedidaCaseira')
    for taco_id, (nome_alimento, medidas) in MEDIDAS.items():
        alimento = Alimento.objects.get(id=id_do_alimento(taco_id))
        if alimento.nome != nome_alimento:
            raise ValueError('Código TACO %s é "%s", não "%s"' % (taco_id, alimento.nome, nome_alimento))
        for nome, gramas in medidas:
            MedidaCaseira.objects.update_or_create(
                id=id_da_medida(taco_id, nome),
                defaults={'alimento': alimento, 'nome': nome, 'gramas': Decimal(gramas)},
            )


def despopular(apps, schema_editor):
    MedidaCaseira = apps.get_model('saude', 'MedidaCaseira')
    ids = [id_da_medida(taco_id, nome) for taco_id, (_, medidas) in MEDIDAS.items() for nome, _ in medidas]
    MedidaCaseira.objects.filter(id__in=ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('saude', '0003_popular_esportes'),
    ]

    operations = [
        migrations.RunPython(popular, despopular),
    ]
