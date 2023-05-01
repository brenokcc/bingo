# Generated by Django 4.1 on 2023-05-01 17:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bingo', '0002_alter_cartela_responsavel_alter_pessoa_observacao'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartela',
            name='realizou_pagamento',
            field=models.BooleanField(null=True, verbose_name='Realizou Pagamento'),
        ),
        migrations.AddField(
            model_name='cartela',
            name='recebeu_comissao',
            field=models.BooleanField(null=True, verbose_name='Recebeu Comissão'),
        ),
    ]
