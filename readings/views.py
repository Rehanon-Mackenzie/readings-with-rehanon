from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from .models import ReadingType
from .forms import ReadingTypeForm


def superuser_required(view_func):
    """Allow only the site owner (superuser) to use a view."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'Sorry, only the site owner has that access.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper

def visible_readings(user):
    """The site owner sees every reading and everyone else only sees active ones."""
    if user.is_superuser:
        return ReadingType.objects.all()
    return ReadingType.objects.filter(is_active=True)

def reading_list(request):
    """Display the readings."""
    readings = visible_readings(request.user)
    return render(request, 'readings/reading_list.html', {'readings': readings})

def reading_detail(request, slug):
    """Display a single reading."""
    reading = get_object_or_404(visible_readings(request.user), slug=slug)
    return render(request, 'readings/reading_detail.html', {'reading': reading})

@superuser_required
def add_reading(request):
    """Let the site owner add a new reading."""
    if request.method == 'POST':
        form = ReadingTypeForm(request.POST, request.FILES)
        if form.is_valid():
            reading = form.save()
            messages.success(request, f'"{reading.name}" has been added.')
            return redirect(reading.get_absolute_url())
        messages.error(request, 'Please correct the errors below.')
    else:
        form = ReadingTypeForm()
    return render(request, 'readings/reading_form.html', {
        'form': form,
        'page_title': 'Add a reading',
        })

@superuser_required
def edit_reading(request, slug):
    """Let the site owner add edit a reading."""
    reading = get_object_or_404(ReadingType, slug=slug)
    if request.method == 'POST':
        form = ReadingTypeForm(request.POST, request.FILES, instance=reading)
        if form.is_valid():
            reading = form.save()
            messages.success(request, f'"{reading.name}" has been updated.')
            return redirect(reading.get_absolute_url())
        messages.error(request, 'Please correct the errors below.')
    else:
        form = ReadingTypeForm(instance=reading)
    return render(request, 'readings/reading_form.html', {
        'form': form,
        'page_title': f'Edit {reading.name}',
        'reading': reading,
        })

@superuser_required
def delete_reading(request, slug):
    """Ask for confirmation then delete a reading."""
    reading = get_object_or_404(ReadingType, slug=slug)
    if request.method == 'POST':
        name = reading.name
        reading.delete()
        messages.success(request, f'"{name}" has been deleted.')
        return redirect('reading_list')
    return render(request, 'readings/reading_confirm_delete.html', {'reading': reading})