from sloth import actions
from .models import Evento

class InformarResponsavel(actions.Action):
    class Meta:
        verbose_name = 'Informar Responsável'
        modal = True
        style = 'primary'
        model = 'bingo.cartela'
        fields = 'responsavel',

    def submit(self):
        super().submit()

    def has_permission(self, user):
        return self.instance.responsavel_id is None


class DevolverCartela(actions.Action):
    class Meta:
        verbose_name = 'Devolver'
        modal = True
        style = 'danger'

    def submit(self):
        self.get_instances().update(responsavel=None, posse=None)
        super().submit()

    def has_permission(self, user):
        return self.instance.id and self.instance.responsavel_id is not None or not self.instance.id


class InformarPosseCartela(actions.Action):
    class Meta:
        verbose_name = 'Informar Posse'
        modal = True
        style = 'primary'
        model = 'bingo.cartela'
        fields = 'posse',

    def submit(self):
        super().submit()

    def has_permission(self, user):
        return self.instance.id and self.instance.responsavel_id is not None or not self.instance.id


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
        if self.cleaned_data['realizou_pagamento'] is None:
            return None
        if self.cleaned_data['realizou_pagamento']:
            if self.cleaned_data['recebeu_comissao'] is None:
                raise actions.ValidationError('Opção inválida')
            return self.cleaned_data['recebeu_comissao']
        return False

    def has_permission(self, user):
        return self.instance.responsavel_id is not None
