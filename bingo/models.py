from sloth.db import models, role, meta
from .roles import ADMINISTRADOR


class PessoaManager(models.Manager):
    def all(self):
        return self.lookups(ADMINISTRADOR)


class Pessoa(models.Model):
    nome = models.CharField('Nome')
    telefone = models.BrRegionalPhoneField('Telefone')
    observacao = models.TextField('Observação', null=True, blank=True)

    objects = PessoaManager()

    class Meta:
        icon = 'person'
        verbose_name = 'Pessoa'
        verbose_name_plural = 'Pessoas'

    def __str__(self):
        return self.nome

    def has_permission(self, user):
        return user.is_superuser or user.roles.contains(ADMINISTRADOR)

    def get_dados_gerais(self):
        return self.value_set(('nome', 'telefone', 'observacao'))

    def get_cartelas(self):
        return (self.cartela_set.all() | self.possecartela_set.all()).display('get_evento', after='talao').aggregations('get_valor_nao_pago', 'get_valor_pendente_pagamento', 'get_valor_pago').expand()

    def view(self):
        return self.value_set('get_dados_gerais', 'get_cartelas')


class EventoManager(models.Manager):
    def all(self):
        return self.lookups(ADMINISTRADOR).display('data', 'get_total_cartelas').cards()


class Evento(models.Model):
    nome = models.CharField('Nome')
    data = models.DateField('Data')

    qtd_taloes = models.IntegerField('Quantidade de Talões')
    qtd_cartela_talao = models.IntegerField('Quantidade de Cartela por Talão')
    valor_venda_cartela = models.DecimalField('Valor de Venda da Cartela')
    valor_comissao_cartela = models.DecimalField('Valor da Comissão por Cartela')

    objects = EventoManager()

    class Meta:
        icon = 'calendar'
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        fieldsets = {
            'Dados Gerais': (('nome', 'data')),
            'Configuração': (('qtd_taloes', 'qtd_cartela_talao'), ('valor_venda_cartela', 'valor_comissao_cartela'))
        }

    def __str__(self):
        return self.nome

    def has_permission(self, user):
        return user.is_superuser or user.roles.contains(ADMINISTRADOR)

    def get_valor_liquido_cartela(self):
        return self.valor_venda_cartela - self.valor_comissao_cartela

    @meta('Receita Esperada')
    def get_receita_esperada(self):
        return self.get_cartelas().filter(responsavel__isnull=False).count() * self.get_valor_liquido_cartela()

    @meta('Recebimento de Venda')
    def get_valor_recebido_venda(self):
        return self.get_cartelas().filter(responsavel__isnull=False, realizou_pagamento=True).count() * self.get_valor_liquido_cartela()

    @meta('Recebimento de Doação')
    def get_valor_recebido_doacao(self):
        return self.get_cartelas().filter(responsavel__isnull=False, realizou_pagamento=True, recebeu_comissao=False).count() * self.valor_comissao_cartela

    @meta('Recebimento Pendente')
    def get_valor_receber(self):
        return self.get_receita_esperada() - self.get_valor_recebido_venda()

    @meta('Recebimento não Realizado')
    def get_valor_nao_recebido(self):
        return self.get_cartelas().filter(responsavel__isnull=False, realizou_pagamento=False).count() * self.get_valor_liquido_cartela()

    @meta('Receita Final')
    def get_receita_final(self):
        return self.get_valor_recebido_venda() + self.get_valor_recebido_doacao()

    def get_dados_gerais(self):
        return self.value_set(('nome', 'data'))

    def get_resumo_finaneiro(self):
        return self.value_set(('get_receita_esperada', 'get_valor_recebido_venda'), ('get_valor_recebido_doacao', 'get_valor_receber'), ('get_valor_nao_recebido', 'get_receita_final'))

    def get_cartelas(self):
        return Cartela.objects.filter(talao__evento=self).all().actions('informar_responsavel', 'informar_posse_cartela').batch_actions('informar_responsavel', 'informar_posse_cartela').aggregations('get_valor_nao_pago', 'get_valor_pendente_pagamento', 'get_valor_pago').expand()

    @meta('Total de Cartelas')
    def get_total_cartelas(self):
        return self.get_cartelas().count()

    def view(self):
        return self.value_set('get_dados_gerais', 'get_cartelas', 'get_resumo_finaneiro')

    def save(self, *args, **kwargs):
        gerar = self.pk is None
        super().save(*args, **kwargs)
        if gerar:
            numero_talao = 1
            numero_cartela = 1
            for i in range(1, self.qtd_taloes+1):
                talao = Talao.objects.create(numero=f'{numero_talao}'.rjust(3, '0'), evento=self)
                for j in range(1, self.qtd_cartela_talao + 1):
                    Cartela.objects.create(numero=f'{numero_cartela}'.rjust(5, '0'), talao=talao)
                    numero_cartela += 1
                numero_talao += 1


class TalaoManager(models.Manager):
    def all(self):
        return self.lookups(ADMINISTRADOR)


class Talao(models.Model):
    numero = models.CharField('Número')
    evento = models.ForeignKey(Evento, verbose_name='Evento')

    objects = TalaoManager()

    class Meta:
        icon = 'journals'
        verbose_name = 'Talão'
        verbose_name_plural = 'Talões'

    def __str__(self):
        return self.numero

    def has_permission(self, user):
        return user.is_superuser or user.roles.contains(ADMINISTRADOR)


class CartelaManager(models.Manager):
    def all(self):
        return self.lookups(ADMINISTRADOR).display('numero', 'talao', 'responsavel', 'posse', 'get_situacao').actions('devolver_cartela', 'prestar_conta').batch_actions('devolver_cartela')

    def pagas(self):
        return self.filter(realizou_pagamento=True)

    def pendentes_pagamento(self):
        return self.filter(realizou_pagamento__isnull=True)

    def nao_pagas(self):
        return self.filter(realizou_pagamento=False)

    def pagas_com_comissao(self):
        return self.pagas().filter(recebeu_comissao=True)

    def pagas_sem_comissao(self):
        return self.pagas().filter(recebeu_comissao=True)

    def get_valor_liquido_cartela(self):
        return self.first().talao.evento.get_valor_liquido_cartela() if self.exists() else 0

    @meta('Pagas')
    def get_valor_pago(self):
        return self.pagas().count() * self.get_valor_liquido_cartela()

    @meta('Pendentes')
    def get_valor_pendente_pagamento(self):
        return self.pendentes_pagamento().count() * self.get_valor_liquido_cartela()

    @meta('Não-Pagas')
    def get_valor_nao_pago(self):
        return self.nao_pagas().count() * self.get_valor_liquido_cartela()


class Cartela(models.Model):
    numero = models.CharField('Número')
    talao = models.ForeignKey(Talao, verbose_name='Talão')

    responsavel = models.ForeignKey(Pessoa, verbose_name='Responsável', null=True)
    realizou_pagamento = models.BooleanField('Realizou Pagamento', null=True)
    recebeu_comissao = models.BooleanField('Recebeu Comissão', null=True)

    posse = models.ForeignKey(Pessoa, verbose_name='Posse', null=True, related_name='possecartela_set', blank=True)

    objects = CartelaManager()

    class Meta:
        icon = 'journal'
        verbose_name = 'Cartega'
        verbose_name_plural = 'Cartela'

    def __str__(self):
        return self.numero

    def get_evento(self):
        return self.talao.evento

    def has_permission(self, user):
        return user.is_superuser or user.roles.contains(ADMINISTRADOR)

    @meta('Situação', renderer='badges/status')
    def get_situacao(self):
        if self.responsavel_id is None:
            return 'primary', 'Aguarando Distribuição'
        elif self.realizou_pagamento is None:
            return 'warning', 'Aguarando Prestação de Contas'
        elif self.realizou_pagamento:
            if self.recebeu_comissao:
                return 'success', 'Vendida com Comissão'
            else:
                return 'success', 'Vendida sem Comissão'
        else:
            return 'danger', 'Pagamento não Realizado'
