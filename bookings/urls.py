from django.urls import path
from . import views

urlpatterns = [
    path('', views.my_bookings, name='my_bookings'),
    path('book/<slug:slug>/', views.book_reading, name='book_reading'),
    path('<int:pk>/cancel/', views.cancel_booking, name='cancel_booking'),
]
