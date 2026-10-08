from django.shortcuts import render, get_object_or_404

from .models import ReadingType


def reading_list(request):
    """Display all active reading types."""
    readings = ReadingType.objects.filter(is_active=True)
    return render(request, 'readings/reading_list.html', {'readings': readings})


def reading_detail(request, slug):
    """Display a single activd reading type"""
    reading = get_object_or_404(ReadingType, slug=slug, is_active=True)
    return render(request, 'readings/reading_detail.html', {'reading': reading})
