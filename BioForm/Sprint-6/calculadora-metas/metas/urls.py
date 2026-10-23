from django.urls import path

from . import views

urlpatterns = [
    path('perfil/metas/', views.perfil_metas, name='perfil_metas'),
]
