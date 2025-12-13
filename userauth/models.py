from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    country_code = models.CharField(max_length=5, blank=True, null=True)
    
    def get_full_phone_number(self):
        if self.country_code and self.phone_number:
            return f"{self.country_code}{self.phone_number}"
        return None

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
