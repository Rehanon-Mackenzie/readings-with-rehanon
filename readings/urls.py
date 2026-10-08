from django.urls import path

from . import views

urlpatterns = [
    path('', views.reading_list, name='reading_list'),
    path('<slug:slug>', views.reading_detail, name='reading_detail'),
]
