from django.db import models
from django.conf import settings

# Create your models here.

class Prediction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='predictions'
    )
    input_data = models.JSONField()
    prediction = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Prediction for {self.user.username} at {self.timestamp}"

class CommunityReport(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_reports'
    )
    food_item = models.CharField(max_length=100)
    commodity_category = models.CharField(max_length=50, blank=True, null=True)
    county = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100)
    market = models.CharField(max_length=100)
    price = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.food_item} at {self.market} ({self.region}) by {self.user.username} on {self.timestamp}"
