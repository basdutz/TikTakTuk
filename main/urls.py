from django.urls import path
from main.views import login, show_main, register_customer, register_organizer

app_name = 'main'

urlpatterns = [
    path('', show_main, name='show_main'),
    path('register/customer/', register_customer, name='register_customer'),
    path('register/organizer/', register_organizer, name='register_organizer'),
    path('login/', login, name='login'),
]