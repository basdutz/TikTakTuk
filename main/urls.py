from django.urls import path
from main.views import (login, register, register_customer, register_organizer, register_admin, 
                        dashboard, dashboard_admin, dashboard_organizer, dashboard_customer, 
                        artist_list,
                        venue_list, venue_create, venue_edit, venue_delete,
                        event_list, event_create, event_edit, order_list_admin, order_list_organizer, order_list_customer, order_checkout, promotion_list_admin, promotion_list_organizer, promotion_list_customer)
from main.views import login, home, register, register_customer, register_organizer, register_admin, dashboard, dashboard_admin, dashboard_organizer, dashboard_customer, artist_list, ticket_category_list

app_name = 'main'

urlpatterns = [
    path('', home, name='home'),
    path('register/', register, name='register'),
    path('register/customer/', register_customer, name='register_customer'),
    path('register/organizer/', register_organizer, name='register_organizer'),
    path('register/admin/', register_admin, name='register_admin'),
    path('login/', login, name='login'),
    path('logout/', login, name='logout'),  # GANTI DENGAN LOGOUT VIEW  
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/admin/', dashboard_admin, name='dashboard_admin'),
    path('dashboard/organizer/', dashboard_organizer, name='dashboard_organizer'),
    path('dashboard/customer/', dashboard_customer, name='dashboard_customer'),
    path('artist/', artist_list, name='artist_list'),

    # Venue
    path('venue/', venue_list, name='venue_list'),
    path('venue/create/', venue_create, name='venue_create'),
    path('venue/<str:venue_id>/edit/', venue_edit, name='venue_edit'),
    path('venue/<str:venue_id>/delete/', venue_delete, name='venue_delete'),

    # Event
    path('event/', event_list, name='event_list'),
    path('event/create/', event_create, name='event_create'),
    path('event/<str:event_id>/edit/', event_edit, name='event_edit'),
    path('ticket-category/', ticket_category_list, name='ticket_category_list'),

    # Order
    path('order/admin/', order_list_admin, name='order_list_admin'),
    path('order/organizer/', order_list_organizer, name='order_list_organizer'),
    path('order/customer/', order_list_customer, name='order_list_customer'),
    path('order/checkout/<str:event_id>/', order_checkout, name='order_checkout'),

    # Promotion
    path('promotion/admin/', promotion_list_admin, name='promotion_list_admin'),
    path('promotion/organizer/', promotion_list_organizer, name='promotion_list_organizer'),
    path('promotion/customer/', promotion_list_customer, name='promotion_list_customer'),
]