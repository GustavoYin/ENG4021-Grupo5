from decimal import Decimal

from django import forms

from .servicos import TIPOS_REFEICAO

GRAMAS = 'g'
MAXIMO_GRAMAS = Decimal('3000')
MAXIMO_MEDIDAS = Decimal('50')


def texto_numero(valor):
    """Decimal sem zeros sobrando, com vírgula: 50.00 -> "50", 12.50 -> "12,5"."""
    texto = format(valor.normalize(), 'f')
    return texto.replace('.', ',')


class ItemForm(forms.Form):
    """Quanto comeu de um alimento: em medida caseira ("2 colheres") ou em gramas."""
    tipo_refeicao = forms.ChoiceField(label='Refeição', choices=TIPOS_REFEICAO)
    medida = forms.ChoiceField(label='Medida')
    quantidade = forms.DecimalField(
        label='Quantidade', min_value=Decimal('0.01'), max_digits=7, decimal_places=2,
        widget=forms.NumberInput(attrs={'step': 'any', 'inputmode': 'decimal'}),
    )

    def __init__(self, alimento, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.alimento = alimento
        self.medidas = {str(m.id): m for m in alimento.medidas.all()}
        escolhas = []
        for chave, medida in self.medidas.items():
            kcal = alimento.kcal * medida.gramas / alimento.porcao_gramas
            escolhas.append((chave, '%s (%s g · %d kcal)' % (medida.nome, texto_numero(medida.gramas), round(kcal))))
        escolhas.append((GRAMAS, 'Gramas'))
        self.fields['medida'].choices = escolhas
        if not self.is_bound:
            primeira = next(iter(self.medidas), GRAMAS)
            self.initial.setdefault('medida', primeira)
            self.initial.setdefault('quantidade', 1 if primeira != GRAMAS else 100)

    def clean(self):
        dados = super().clean()
        medida, quantidade = dados.get('medida'), dados.get('quantidade')
        if medida is None or quantidade is None:
            return dados
        if medida == GRAMAS:
            if quantidade > MAXIMO_GRAMAS:
                self.add_error('quantidade', 'Use no máximo %s g por vez.' % MAXIMO_GRAMAS)
                return dados
            porcoes = (quantidade / self.alimento.porcao_gramas).quantize(Decimal('0.01'))
            if porcoes <= 0:
                self.add_error('quantidade', 'Quantidade pequena demais.')
                return dados
            dados['medida_caseira'], dados['quantidade_final'] = None, porcoes
        else:
            if quantidade > MAXIMO_MEDIDAS:
                self.add_error('quantidade', 'Use no máximo %s por vez.' % MAXIMO_MEDIDAS)
                return dados
            dados['medida_caseira'], dados['quantidade_final'] = self.medidas[medida], quantidade
        return dados


class ComboForm(forms.Form):
    nome = forms.CharField(label='Nome do combo', max_length=100, min_length=2)
