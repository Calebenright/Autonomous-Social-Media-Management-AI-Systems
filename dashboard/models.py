from django.db import models
from django.contrib.auth.models import User

class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    business_description = models.TextField(blank=True)
    website = models.TextField(blank=True)
    brand_color = models.CharField(max_length=7, blank=True)  # Assuming hexadecimal color code
    logo = models.FileField(upload_to='logos/', blank=True)
    temperature = models.IntegerField(default=1)
    next_image_url = models.URLField(blank=True)
    next_caption = models.TextField(blank=True)
    last_image_url = models.URLField(blank=True)
    last_caption = models.TextField(blank=True)
    