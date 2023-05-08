# Generated by Django 4.1 on 2023-05-01 16:55

from django.db import migrations, models
import django.db.models.deletion
import sloth.core.base
import sloth.db.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Evento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', sloth.db.models.CharField(max_length=255, verbose_name='Nome')),
                ('data', models.DateField(verbose_name='Data')),
                ('qtd_taloes', models.IntegerField(verbose_name='Quantidade de Talões')),
                ('qtd_cartela_talao', models.IntegerField(verbose_name='Quantidade de Cartela por Talão')),
                ('valor_venda_cartela', sloth.db.models.DecimalField(decimal_places=2, max_digits=9, verbose_name='Valor de Venda da Cartela')),
                ('valor_comissao_cartela', sloth.db.models.DecimalField(decimal_places=2, max_digits=9, verbose_name='Valor Máximo da Comissão por Cartela')),
            ],
            options={
                'verbose_name': 'Evento',
                'verbose_name_plural': 'Eventos',
                'icon': 'calendar',
            },
            bases=(models.Model, sloth.core.base.ModelMixin),
        ),
        migrations.CreateModel(
            name='Pessoa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', sloth.db.models.CharField(max_length=255, verbose_name='Nome')),
                ('telefone', sloth.db.models.BrRegionalPhoneField(max_length=255, verbose_name='Telefone')),
                ('observacao', sloth.db.models.TextField(verbose_name='Observação')),
            ],
            options={
                'verbose_name': 'Pessoa',
                'verbose_name_plural': 'Pessoas',
                'icon': 'person',
            },
            bases=(models.Model, sloth.core.base.ModelMixin),
        ),
        migrations.CreateModel(
            name='Talao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', sloth.db.models.CharField(max_length=255, verbose_name='Número')),
                ('evento', sloth.db.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bingo.evento', verbose_name='Evento')),
            ],
            options={
                'verbose_name': 'Talão',
                'verbose_name_plural': 'Talões',
                'icon': 'journals',
            },
            bases=(models.Model, sloth.core.base.ModelMixin),
        ),
        migrations.CreateModel(
            name='Cartela',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', sloth.db.models.CharField(max_length=255, verbose_name='Número')),
                ('responsavel', sloth.db.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bingo.pessoa', verbose_name='Responsável')),
                ('talao', sloth.db.models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bingo.talao', verbose_name='Talão')),
            ],
            options={
                'verbose_name': 'Cartega',
                'verbose_name_plural': 'Cartelas',
                'icon': 'journal',
            },
            bases=(models.Model, sloth.core.base.ModelMixin),
        ),
    ]
