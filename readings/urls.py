from django.urls import path

from . import views

urlpatterns = [
    path('', views.reading_list, name='reading_list'),
    path('add/', views.add_reading, name='add_reading'),
    path('<slug:slug>', views.reading_detail, name='reading_detail'),
    path('<slug:slug>/edit', views.edit_reading, name='edit_reading'),
    path('<slug:slug>/delete', views.delete_reading, name='delete_reading'),
]
