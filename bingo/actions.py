from sloth import actions
from sloth.utils.http import XlsResponse
from .models import Evento
from .roles import ADMINISTRADOR, OPERADOR

class InformarResponsavel(actions.Action):
    class Meta:
        verbose_name = 'Distribuir'
        modal = True
        style = 'primary'
        model = 'bingo.cartela'
        fields = 'responsavel',

    def submit(self):
        super().submit()

    def has_permission(self, user):
        return user.roles.contains(ADMINISTRADOR, OPERADOR) and self.instance.responsavel_id is None


class DevolverCartela(actions.Action):
    class Meta:
        verbose_name = 'Devolver'
        modal = True
        style = 'danger'

    def submit(self):
        self.get_instances().update(responsavel=None, posse=None)
        super().submit()

    def has_permission(self, user):
        return (user.is_superuser or user.roles.contains(ADMINISTRADOR, OPERADOR)) and (self.instance.id is None or (self.instance.id and self.instance.responsavel_id is not None and self.instance.realizou_pagamento is None))


class InformarPosseCartela(actions.Action):
    class Meta:
        verbose_name = 'Informar Posse'
        modal = True
        style = 'primary'
        model = 'bingo.cartela'
        fields = 'posse',

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['posse'].addable = True

    def submit(self):
        super().submit()

    def has_permission(self, user):
        return user.roles.contains(ADMINISTRADOR, OPERADOR) and self.instance.id and self.instance.responsavel_id is not None or not self.instance.id


class PrestarConta(actions.Action):
    class Meta:
        verbose_name = 'Prestar Contas'
        modal = True
        style = 'success'
        model = 'bingo.cartela'
        fieldsets = {
            None: ('realizou_pagamento', ('meio_pagamento', 'comissao')),
        }

    def view(self):
        self.on_realizou_pagamento_change(self.instance.realizou_pagamento)

    def submit(self):
        super().submit()

    def on_realizou_pagamento_change(self, value):
        self.show('comissao', 'meio_pagamento') if value else self.hide('comissao', 'meio_pagamento')

    def clean_comissao(self):
        if self.cleaned_data['realizou_pagamento'] is None:
            return 0
        if self.cleaned_data['realizou_pagamento']:
            if self.cleaned_data['comissao'] is None:
                raise actions.ValidationError('Informe a comissão')
            if self.cleaned_data['comissao'] > self.instantiator.valor_comissao_cartela:
                raise actions.ValidationError('Valor não pode ser superior a {}'.format(self.instantiator.valor_comissao_cartela))
            return self.cleaned_data['comissao']
        return 0

    def has_permission(self, user):
        return user.roles.contains(ADMINISTRADOR, OPERADOR) and self.instance.responsavel_id is not None or not self.instance.id

class ExportarCartelasExcel(actions.Action):
    class Meta:
        verbose_name = 'Exportar para Excel'
        modal = True
        style = 'primary'

    def submit(self):
        rows = []
        valor = None
        rows.append(('Nº da Cartela', 'Talão', 'Responsável', 'Posse', 'Valor da Cartela', 'Valor da Comissão', 'Situação'))
        print(self.get_instances().query)
        for obj in self.get_instances().order_by('numero'):
            if valor is None:
                valor = obj.talao.evento.get_valor_liquido_cartela()
            rows.append((obj.numero, obj.talao.numero, obj.responsavel.nome if obj.responsavel else '', obj.posse.nome if obj.posse else '', valor, obj.comissao or '0', obj.get_situacao()[1]))
        return XlsResponse([('Cartelas', rows)])

    def has_permission(self, user):
        return user.is_superuser or user.roles.contains(ADMINISTRADOR, OPERADOR)


class GerarMaisCartelas(actions.Action):
    qtd_taloes = actions.IntegerField(label='Quantidade de Talões')

    class Meta:
        verbose_name = 'Gerar Mais Cartelas'
        modal = True
        style = 'primary'

    def submit(self):
        ultima_cartela = self.objects('bingo.cartela').filter(talao__evento=self.instance).order_by('id').last()
        self.instance.gerar_cartelas(int(ultima_cartela.talao.numero)+1, int(ultima_cartela.numero)+1, self.cleaned_data['qtd_taloes'])
        super().submit()

    def has_permission(self, user):
        return user.is_superuser or user.roles.contains(ADMINISTRADOR)
