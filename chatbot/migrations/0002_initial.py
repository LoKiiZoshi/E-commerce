# Generated by Django 5.1.6 on 2025-05-10 10:33

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('chatbot', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='chatsession',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='session',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='chatbot.chatsession'),
        ),
        migrations.AddField(
            model_name='response',
            name='intent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='chatbot.intent'),
        ),
        migrations.AddField(
            model_name='trainingphrase',
            name='intent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='training_phrases', to='chatbot.intent'),
        ),
    ]
