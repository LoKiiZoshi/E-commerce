from django.db import models
from django.conf import settings

class ChatSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Chat Session {self.session_id}"

class ChatMessage(models.Model):
    MESSAGE_TYPE_CHOICES = (
        ('user', 'User'),
        ('bot', 'Bot'),
    )
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}"

class Intent(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class TrainingPhrase(models.Model):
    intent = models.ForeignKey(Intent, on_delete=models.CASCADE, related_name='training_phrases')
    text = models.TextField()
    
    def __str__(self):
        return self.text

class Response(models.Model):
    intent = models.ForeignKey(Intent, on_delete=models.CASCADE, related_name='responses')
    text = models.TextField()
    
    def __str__(self):
        return self.text