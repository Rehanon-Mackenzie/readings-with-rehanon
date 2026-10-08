from django.db import models
from django.urls import reverse

class ReadingType(models.Model):
    """A type of reading that clients can book."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    summary = models.CharField(
        max_length=200,
        help_text='One or two sentences shown on the readings page.'
    )
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    duration_minutes = models.PositiveIntegerField()
    is_active = models.BooleanField(
        default=True,
        help_text='Untick to hide this reading without deleting it.'
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('reading_detail', args=[self.slug])
