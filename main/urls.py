from django.urls import path
from main.views import (
    home, login, logout, manajemen_tiket_admin, manajemen_tiket_organizer, register, register_customer, register_organizer, register_admin, 
    dashboard, dashboard_admin, dashboard_organizer, dashboard_customer, 
    artist_list, profile_customer, profile_organizer, seat_admin, seat_organizer, 
    venue_list, venue_create, venue_edit, venue_delete,
    event_list, event_create, event_edit,
    ticket_category_list, my_tickets,
    order_list_admin, order_list_organizer, order_list_customer, order_checkout,
    promotion_list_admin, promotion_list_organizer, promotion_list_customer
)

app_name = 'main'

urlpatterns = [
    path('', home, name='home'),
    path('register/', register, name='register'),
    path('register/customer/', register_customer, name='register_customer'),
    path('register/organizer/', register_organizer, name='register_organizer'),
    path('register/admin/', register_admin, name='register_admin'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'), 
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/admin/', dashboard_admin, name='dashboard_admin'),
    path('dashboard/organizer/', dashboard_organizer, name='dashboard_organizer'),
    path('dashboard/customer/', dashboard_customer, name='dashboard_customer'),

    # Artist & Profile
    path('artist/', artist_list, name='artist_list'),
    path('profile/customer/', profile_customer, name='profile_customer'),
    path('profile/organizer/', profile_organizer, name='profile_organizer'),

    # Venue
    path('venue/', venue_list, name='venue_list'),
    path('venue/create/', venue_create, name='venue_create'),
    path('venue/<str:venue_id>/edit/', venue_edit, name='venue_edit'),
    path('venue/<str:venue_id>/delete/', venue_delete, name='venue_delete'),

    # Event
    path('event/', event_list, name='event_list'),
    path('event/create/', event_create, name='event_create'),
    path('event/<str:event_id>/edit/', event_edit, name='event_edit'),

    # Ticket
    path('ticket-category/', ticket_category_list, name='ticket_category_list'),
    path('ticket/customer/', my_tickets, name='my_tickets'),
    path('ticket/admin/', manajemen_tiket_admin, name='manajemen_tiket_admin'),
    path('ticket/organizer/', manajemen_tiket_organizer, name='manajemen_tiket_organizer'),
    path('seat/admin/', seat_admin, name='seat_admin'),
    path('seat/organizer/', seat_organizer, name='seat_organizer'),

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