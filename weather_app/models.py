from django.db import models

class SearchHistory(models.Model):
    city_name = models.CharField(max_length=255)
    searched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-searched_at']

    def __str__(self):
        return f"{self.city_name} searched at {self.searched_at.strftime('%Y-%m-%d %H:%M')}"

