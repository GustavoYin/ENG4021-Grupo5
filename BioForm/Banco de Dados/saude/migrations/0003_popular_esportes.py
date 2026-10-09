"""
Popula o catálogo de esportes com os que aparecem no mockup do perfil (passo 3)
e no Documento de Regras de Negócio.

MET = gasto energético de referência para uso geral, aproximado a partir do
Compendium of Physical Activities (Ainsworth et al.). Gasto em kcal ≈ MET x peso (kg) x horas.
São valores médios: o grupo pode ajustá-los pelo admin.
"""
import uuid
from decimal import Decimal

from django.db import migrations

NAMESPACE_ESPORTES = uuid.UUID('0b7a3e52-2f4d-4f0e-8a1c-5e2d9c4b7f31')

ESPORTES = [
    ('Musculação', '5.0'),
    ('Corrida', '8.0'),
    ('Ciclismo', '7.5'),
    ('Natação', '6.0'),
    ('Funcional', '8.0'),
    ('Futebol', '7.0'),
    ('Lutas', '10.3'),
    ('Yoga', '2.5'),
    ('Vôlei', '4.0'),
    ('Futevôlei', '8.0'),
]


def id_do_esporte(nome):
    return uuid.uuid5(NAMESPACE_ESPORTES, nome)


def popular(apps, schema_editor):
    Esporte = apps.get_model('saude', 'Esporte')
    for nome, met in ESPORTES:
        Esporte.objects.update_or_create(
            id=id_do_esporte(nome),
            defaults={'nome': nome, 'met': Decimal(met)},
        )


def despopular(apps, schema_editor):
    Esporte = apps.get_model('saude', 'Esporte')
    Esporte.objects.filter(id__in=[id_do_esporte(nome) for nome, _ in ESPORTES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('saude', '0002_popular_alimentos_taco'),
    ]

    operations = [
        migrations.RunPython(popular, despopular),
    ]
