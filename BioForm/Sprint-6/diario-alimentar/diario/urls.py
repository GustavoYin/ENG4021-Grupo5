from datetime import date

from django.urls import path, register_converter

from . import views


class DataConverter:
    """Datas no endereço no formato 2026-10-22 (data inválida vira 404)."""
    regex = r'\d{4}-\d{2}-\d{2}'

    def to_python(self, valor):
        return date.fromisoformat(valor)

    def to_url(self, valor):
        return valor.isoformat()


register_converter(DataConverter, 'data')

urlpatterns = [
    path('diario/', views.dia, name='diario_hoje'),
    path('diario/historico/', views.historico, name='diario_historico'),
    path('diario/<data:data>/', views.dia, name='diario_dia'),
    path('diario/<data:data>/adicionar/', views.adicionar, name='diario_adicionar'),
    path('diario/<data:data>/agua/', views.agua, name='diario_agua'),
    path('diario/<data:data>/checkin/', views.checkin, name='diario_checkin'),
    path('diario/<data:data>/combo/', views.usar_combo, name='diario_usar_combo'),
    path('diario/item/<uuid:item_id>/remover/', views.remover_item, name='diario_remover_item'),
    path('diario/refeicao/<uuid:registro_id>/salvar-combo/', views.salvar_combo, name='diario_salvar_combo'),
    path('diario/combo/<uuid:combo_id>/excluir/', views.excluir_combo, name='diario_excluir_combo'),
]
