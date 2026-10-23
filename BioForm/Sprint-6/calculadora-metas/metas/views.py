from django.shortcuts import redirect, render

from contas.onboarding import em_onboarding, perfil_obrigatorio, proximo_passo
from saude.models import OBJETIVOS

from .calculo import PROTEINA_G_POR_KG, equivalencias, metas_do_usuario


@perfil_obrigatorio
def perfil_metas(request, usuario):
    passo = proximo_passo(usuario)
    if passo:
        return redirect(passo)
    metas = metas_do_usuario(usuario)
    medida = usuario.medida_atual()
    esportes = list(usuario.esportes.select_related('esporte'))
    return render(request, 'metas/perfil_metas.html', {
        'usuario': usuario,
        'medida': medida,
        'objetivo': OBJETIVOS[medida.objetivo_momento],
        'esportes': esportes,
        'metas': metas,
        'pratica': equivalencias(metas),
        'proteina_por_kg': PROTEINA_G_POR_KG[medida.objetivo_momento],
        'passo': 4,
        'onboarding': em_onboarding(request, usuario),
    })
