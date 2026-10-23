from datetime import timedelta

from django import template
from django.utils import timezone

register = template.Library()

DIAS_DA_SEMANA = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']


@register.filter
def nome_do_dia(data):
    """"Hoje", "Ontem" ou "quinta, 16/10"."""
    hoje = timezone.localdate()
    if data == hoje:
        return 'Hoje'
    if data == hoje - timedelta(days=1):
        return 'Ontem'
    return '%s, %s' % (DIAS_DA_SEMANA[data.weekday()], data.strftime('%d/%m'))


@register.filter
def inteiro(valor):
    """Arredonda para inteiro (kcal e gramas na tela)."""
    try:
        return int(round(valor))
    except (TypeError, ValueError):
        return valor


@register.filter
def porcao(item):
    """Como o item foi registrado: "2 × 1 colher de sopa" ou "150 g"."""
    gramas = int(round(item.gramas()))
    if item.medida_caseira:
        quantidade = format(item.quantidade.normalize(), 'f').replace('.', ',')
        prefixo = '' if item.quantidade == 1 else '%s × ' % quantidade
        return '%s%s · %d g' % (prefixo, item.medida_caseira.nome, gramas)
    return '%d g' % gramas
