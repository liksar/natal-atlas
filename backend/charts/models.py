import secrets
import uuid
from django.db import models
from .search import normalize

def token():
    return secrets.token_urlsafe(32)

class Client(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    internal_name = models.CharField(max_length=120)
    search_name = models.TextField(default='', editable=False)
    internal_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.internal_name
    def save(self, *args, **kwargs):
        self.search_name = normalize(self.internal_name)
        if kwargs.get('update_fields'):
            kwargs['update_fields'] = set(kwargs['update_fields']) | {'search_name'}
        super().save(*args, **kwargs)

class City(models.Model):
    source_id = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=2)
    region = models.CharField(max_length=200, blank=True)
    aliases = models.TextField(blank=True)
    search_text = models.TextField(default='', editable=False)
    latitude = models.FloatField()
    longitude = models.FloatField()
    timezone_id = models.CharField(max_length=64)
    dataset_version = models.CharField(max_length=100)
    class Meta:
        indexes = [models.Index(fields=['country', 'name'])]
    def __str__(self):
        return f'{self.name}, {self.region}, {self.country}'
    def save(self, *args, **kwargs):
        self.search_text = normalize(self.name+','+self.aliases)
        if kwargs.get('update_fields'):
            kwargs['update_fields'] = set(kwargs['update_fields']) | {'search_text'}
        super().save(*args, **kwargs)

class Chart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.OneToOneField(Client, on_delete=models.CASCADE)
    public_token = models.CharField(max_length=64, unique=True, default=token, editable=False)
    display_name = models.CharField(max_length=120)
    language = models.CharField(max_length=2, choices=[('en','English'),('uk','Українська'),('ru','Русский')], default='uk')
    search_name = models.TextField(default='', editable=False)
    revision = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def save(self, *args, **kwargs):
        self.search_name = normalize(self.display_name)
        if kwargs.get('update_fields'):
            kwargs['update_fields'] = set(kwargs['update_fields']) | {'search_name'}
        super().save(*args, **kwargs)

class ChartRevision(models.Model):
    chart = models.ForeignKey(Chart, on_delete=models.CASCADE, related_name='revisions')
    revision = models.PositiveIntegerField()
    input = models.JSONField()
    place_search = models.TextField(default='', editable=False)
    result = models.JSONField()
    language = models.CharField(max_length=2, choices=[('en','English'),('uk','Українська'),('ru','Русский')], default='uk')
    presentation = models.JSONField(default=dict)
    fingerprint = models.CharField(max_length=64)
    actor = models.ForeignKey('auth.User', null=True, on_delete=models.SET_NULL)
    reason = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['chart', 'revision'], name='unique_chart_revision')]

class AuditEvent(models.Model):
    actor = models.ForeignKey('auth.User', null=True, on_delete=models.SET_NULL)
    chart_uuid = models.UUIDField(null=True)
    action = models.CharField(max_length=32)
    revision = models.PositiveIntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Submission(models.Model):
    key = models.UUIDField(primary_key=True)
    actor = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    chart = models.ForeignKey(Chart, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

class RateBucket(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    window = models.BigIntegerField()
    count = models.PositiveIntegerField(default=0)
