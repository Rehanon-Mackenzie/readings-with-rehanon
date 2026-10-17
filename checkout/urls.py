from django.urls import path
from . import views

urlpatterns = [
    path('<int:booking_id>/', views.checkout, name='checkout'),
    path('<int:booking_id>/success/', views.checkout_success, name='checkout_success'), 
]