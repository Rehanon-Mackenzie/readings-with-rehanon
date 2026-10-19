from django.shortcuts import render

from readings.models import ReadingType

# Create your views here.


def index(request):
    """Home page, showing a few active readings to browse."""
    featured_readings = ReadingType.objects.filter(is_active=True)[:3]
    return render(request, 'home/index.html',
                  {'featured_readings': featured_readings})
