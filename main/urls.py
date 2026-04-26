from django.urls import path
from main.views import login, register, register_customer, register_organizer, register_admin, dashboard, dashboard_admin, dashboard_organizer, dashboard_customer, artist_list

app_name = 'main'

urlpatterns = [
    path('', register, name='register'),
    path('register/customer/', register_customer, name='register_customer'),
    path('register/organizer/', register_organizer, name='register_organizer'),
    path('register/admin/', register_admin, name='register_admin'),
    path('login/', login, name='login'),
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/admin/', dashboard_admin, name='dashboard_admin'),
    path('dashboard/organizer/', dashboard_organizer, name='dashboard_organizer'),
    path('dashboard/customer/', dashboard_customer, name='dashboard_customer'),
    path('artist/', artist_list, name='artist_list'),
]