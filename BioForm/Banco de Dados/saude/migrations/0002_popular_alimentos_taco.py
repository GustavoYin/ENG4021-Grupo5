"""
Popula o catálogo de alimentos com a TACO - Tabela Brasileira de Composição
de Alimentos (NEPA/UNICAMP, 4ª edição, 2011). Valores por 100 g da parte comestível.

Fonte dos dados em CSV: https://github.com/raulfdm/taco-api (licença MIT).
Campos sem valor na TACO (traço / não se aplica, ex.: proteína do azeite) viram 0.
Alimentos sem nenhuma análise na TACO foram deixados de fora.
"""
import csv
import uuid
from decimal import Decimal
from pathlib import Path

from django.db import migrations

ARQUIVO_CSV = Path(__file__).resolve().parent.parent / 'dados' / 'alimentos_taco.csv'

# UUID fixo derivado do código TACO: rodar de novo não duplica alimentos
NAMESPACE_TACO = uuid.UUID('6f1d1c3a-6a8e-4c55-9a39-0d9b6e2f7a10')


def id_do_alimento(taco_id):
    return uuid.uuid5(NAMESPACE_TACO, 'taco-%s' % taco_id)


def popular(apps, schema_editor):
    Alimento = apps.get_model('saude', 'Alimento')
    with open(ARQUIVO_CSV, encoding='utf-8') as arquivo:
        for linha in csv.DictReader(arquivo):
            Alimento.objects.update_or_create(
                id=id_do_alimento(linha['taco_id']),
                defaults={
                    'nome': linha['nome'],
                    'porcao_padrao': '100g',
                    'porcao_gramas': Decimal('100'),
                    'kcal': Decimal(linha['kcal']),
                    'proteina_g': Decimal(linha['proteina_g']),
                    'carbo_g': Decimal(linha['carbo_g']),
                    'gordura_g': Decimal(linha['gordura_g']),
                },
            )


def despopular(apps, schema_editor):
    Alimento = apps.get_model('saude', 'Alimento')
    with open(ARQUIVO_CSV, encoding='utf-8') as arquivo:
        ids = [id_do_alimento(linha['taco_id']) for linha in csv.DictReader(arquivo)]
    Alimento.objects.filter(id__in=ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('saude', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(popular, despopular),
    ]
