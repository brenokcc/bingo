from sloth import actions
from .models import Evento

class AtribuirCartela(actions.Action):
    class Meta:
        verbose_name = 'Atribuir Cartela'
        modal = True
        style = 'primary'
        model = 'bingo.cartela'
        fields = 'responsavel',

    def submit(self):
        super().submit()

    def has_permission(self, user):
        return isinstance(self.instantiator, Evento) and self.instance.responsavel_id is None


class DevolverCartela(actions.Action):
    class Meta:
        verbose_name = 'Devolver Cartela'
        modal = True
        style = 'danger'

    def submit(self):
        self.instance.responsavel_id = None
        self.instance.save()
        super().submit()

    def has_permission(self, user):
        return self.instance.responsavel_id is not None


class PrestarConta(actions.Action):
    class Meta:
        verbose_name = 'Prestar Contas'
        modal = True
        style = 'warning'
        model = 'bingo.cartela'
        fields = 'realizou_pagamento', 'recebeu_comissao'

    def submit(self):
        super().submit()

    def clean_recebeu_comissao(self):
        if self.cleaned_data['recebeu_comissao'] is not None and not self.cleaned_data['realizou_pagamento']:
            raise actions.ValidationError('Opção inválida')
        return self.cleaned_data['recebeu_comissao']

    def has_permission(self, user):
        return self.instance.responsavel_id is not None
