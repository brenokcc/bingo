from sloth.db import models, role, meta
from .roles import ADMINISTRADOR, OPERADOR


class MeioPagamentoManager(models.Manager):
    def all(self):
        return self.lookups(ADMINISTRADOR)


class MeioPagamento(models.Model):
    nome = models.CharField('Nome')

    objects = MeioPagamentoManager()

    class Meta:
        icon = 'currency-dollar'
        verbose_name = 'Meio de Pagamento'
        verbose_name_plural = 'Meios de Pagamento'

    def __str__(self):
        return self.nome

    def has_permission(self, user):
        return user.is_superuser or user.roles.contains(ADMINISTRADOR)


class PessoaManager(models.Manager):
    def all(self):
        return self.lookups(ADMINISTRADOR, OPERADOR)


class Pessoa(models.Model):
    nome = models.CharField('Nome')
    cpf = models.BrCpfField('CPF', null=True, blank=True)
    telefone = models.BrRegionalPhoneField('Telefone', null=True, blank=True)
    observacao = models.TextField('Observação', null=True, blank=True)

    objects = PessoaManager()

    class Meta:
        icon = 'person'
        verbose_name = 'Pessoa'
        verbose_name_plural = 'Pessoas'

    def __str__(self):
        return self.nome

    def has_view_permission(self, user):
        return user.roles.contains(OPERADOR)

    def has_add_permission(self, user):
        return user.roles.contains(OPERADOR)

    def has_edit_permission(self, user):
        return user.roles.contains(OPERADOR)

    def has_permission(self, user):
        return user.is_superuser or user.roles.contains(ADMINISTRADOR)

    def get_dados_gerais(self):
        return self.value_set(('nome', 'telefone', 'observacao'))

    def get_cartelas(self):
        return (self.cartela_set.all() | self.possecartela_set.all()).display('get_evento', after='talao').aggregations('get_valor_nao_pago', 'get_valor_pendente_pagamento', 'get_valor_pago').expand()

    def view(self):
        return self.value_set('get_dados_gerais', 'get_cartelas')


class AdministradorManager(models.Manager):
    def all(self):
        return self.lookups(ADMINISTRADOR).display('pessoa__cpf', 'pessoa__nome')


@role(ADMINISTRADOR, username='pessoa__cpf')
class Administrador(models.Model):
    pessoa = models.ForeignKey(Pessoa, verbose_name='Pessoa')

    objects = AdministradorManager()

    class Meta:
        icon = 'person-check'
        verbose_name = 'Administrador'
        verbose_name_plural = 'Administradores'

    def __str__(self):
        return '{}'.format(self.pk)

    def has_permission(self, user):
        return user.is_superuser or user.roles.contains(ADMINISTRADOR)


class EventoManager(models.Manager):
    def all(self):
        return self.lookups(ADMINISTRADOR).lookups(OPERADOR, operadores__cpf='username').display('data', 'get_total_cartelas').cards()


@role(OPERADOR, username='operadores__cpf')
class Evento(models.Model):
    nome = models.CharField('Nome')
    data = models.DateField('Data')
    operadores = models.ManyToManyField(Pessoa, verbose_name='Operadores', addable=True)

    qtd_taloes = models.IntegerField('Quantidade de Talões')
    qtd_cartela_talao = models.IntegerField('Quantidade de Cartela por Talão')
    valor_venda_cartela = models.DecimalField('Valor de Venda da Cartela')
    valor_comissao_cartela = models.DecimalField('Valor Máximo da Comissão por Cartela')

    objects = EventoManager()

    class Meta:
        icon = 'calendar'
        verbose_name = 'Evento'
        verbose_name_plural = 'Eventos'
        fieldsets = {
            'Dados Gerais': (('nome', 'data'),'operadores'),
            'Configuração': (('qtd_cartela_talao', 'qtd_taloes'), ('valor_venda_cartela', 'valor_comissao_cartela'))
        }
        edit_fieldsets = {
            'Dados Gerais': (('nome', 'data'), 'operadores'),
        }

    def __str__(self):
        return self.nome

    def has_permission(self, user):
        return user.is_superuser or user.roles.contains(ADMINISTRADOR)

    def has_view_permission(self, user):
        return user.roles.contains(OPERADOR)

    def get_valor_liquido_cartela(self):
        return self.valor_venda_cartela - self.valor_comissao_cartela

    def get_cartelas_distribuidas(self):
        return self.get_cartelas().filter(responsavel__isnull=False)

    def get_total_taloes(self):
        return self.get_total_cartelas() // self.qtd_cartela_talao

    @meta('Percentual de Cartela Distribuída', renderer='progress/primary')
    def get_percentual_cartela_distribuida(self):
        return int(100 * self.get_cartelas_distribuidas().count() / self.get_total_cartelas())

    @meta('Percentual de Cartela Paga', renderer='progress/success')
    def get_percentual_cartela_paga(self):
        return int(100 * self.get_cartelas_distribuidas().filter(realizou_pagamento=True).count() / self.get_total_cartelas())

    @meta('Total de Cartelas Distribuídas')
    def get_total_cartelas_distribuidas(self):
        return self.get_cartelas_distribuidas().count()

    @meta('Receita Esperada')
    def get_receita_esperada(self):
        return self.get_cartelas_distribuidas().count() * self.get_valor_liquido_cartela()

    @meta('Recebimento de Venda')
    def get_valor_recebido_venda(self):
        return self.get_cartelas_distribuidas().filter(realizou_pagamento=True).count() * self.get_valor_liquido_cartela()

    @meta('Recebimento de Doação')
    def get_valor_recebido_doacao(self):
        qs = self.get_cartelas_distribuidas().filter(realizou_pagamento=True)
        return qs.count() * self.valor_comissao_cartela - qs.sum('comissao')

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
        return self.value_set(('nome', 'data'), ('get_total_taloes', 'get_total_cartelas'), 'get_percentual_cartela_distribuida', 'get_percentual_cartela_paga')

    def get_resumo_finaneiro(self):
        return self.value_set(('get_total_cartelas_distribuidas', 'get_receita_esperada', 'get_valor_recebido_venda'), ('get_valor_recebido_doacao', 'get_valor_receber', 'get_valor_nao_recebido'), 'get_receita_final')

    def get_cartelas(self):
        return Cartela.objects.filter(talao__evento=self).all().actions('informar_responsavel', 'informar_posse_cartela').aggregations('get_valor_nao_pago', 'get_valor_pendente_pagamento', 'get_valor_pago').expand()

    @meta('Total de Cartelas')
    def get_total_cartelas(self):
        return self.get_cartelas().count()

    def view(self):
        return self.value_set('get_dados_gerais', 'get_cartelas', 'get_resumo_finaneiro').actions('gerar_mais_cartelas')

    def save(self, *args, **kwargs):
        gerar_cartelas = self.pk is None
        super().save(*args, **kwargs)
        if gerar_cartelas:
            self.gerar_cartelas(qtd_taloes=self.qtd_taloes)

    def gerar_cartelas(self, numero_talao=1, numero_cartela=1, qtd_taloes=10):
        for i in range(1, qtd_taloes+1):
            talao = Talao.objects.create(numero=f'{numero_talao}'.rjust(3, '0'), evento=self)
            for j in range(1, self.qtd_cartela_talao + 1):
                Cartela.objects.create(numero=f'{numero_cartela}'.rjust(5, '0'), talao=talao)
                numero_cartela += 1
            numero_talao += 1


class TalaoManager(models.Manager):
    def all(self):
        return self.lookups(ADMINISTRADOR).lookups(OPERADOR, evento__operadores__cpf='username')


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
        return self.lookups(ADMINISTRADOR).lookups(OPERADOR, talao__evento__operadores__cpf='username').display('numero', 'talao', 'responsavel', 'posse', 'realizou_pagamento', 'meio_pagamento', 'comissao', 'get_situacao').actions('devolver_cartela', 'prestar_conta').global_actions('exportar_cartelas_excel').attach('pendentes_distribuicao', 'pendentes_pagamento', 'pagas')

    @meta('Aguardando Distribuição')
    def pendentes_distribuicao(self):
        return self.filter(responsavel__isnull=True).batch_actions('informar_responsavel')

    def pagas(self):
        return self.filter(responsavel__isnull=False, realizou_pagamento=True)

    @meta('Aguardando Pagamento')
    def pendentes_pagamento(self):
        return self.filter(responsavel__isnull=False, realizou_pagamento__isnull=True).batch_actions('devolver_cartela', 'informar_posse_cartela', 'prestar_conta')

    def nao_pagas(self):
        return self.filter(responsavel__isnull=False, realizou_pagamento=False)

    def pagas_com_comissao(self):
        return self.pagas().filter(comissao__gt=0)

    def pagas_sem_comissao(self):
        return self.pagas().filter(recebeu=0)

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
    meio_pagamento = models.ForeignKey(MeioPagamento, verbose_name='Meio de Pagamento', null=True, blank=True)
    comissao = models.DecimalField('Comissão', default=0)

    posse = models.ForeignKey(Pessoa, verbose_name='Posse', null=True, related_name='possecartela_set', blank=True)

    objects = CartelaManager()

    class Meta:
        icon = 'journal'
        verbose_name = 'Cartega'
        verbose_name_plural = 'Cartelas'

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
            if self.comissao > 0:
                return 'success', 'Vendida com Comissão'
            else:
                return 'success', 'Vendida sem Comissão'
        else:
            return 'danger', 'Pagamento não Realizado'
