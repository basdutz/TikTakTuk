from django.urls import path
from main.views import (
    home, login, logout, manajemen_tiket_admin, manajemen_tiket_organizer, profile_admin_update, profile_admin_password, profile_customer_password, profile_customer_update, profile_organizer_password, profile_organizer_update, register, register_customer, register_organizer, register_admin, 
    dashboard, dashboard_admin, dashboard_organizer, dashboard_customer, 
    artist_list, profile_customer, profile_organizer, profile_admin, seat_admin, seat_organizer, seat_delete, seat_create, seat_update,
    venue_list, venue_create, venue_edit, venue_delete,
    event_list, event_create, event_edit,
    ticket_category_list, my_tickets, ticket_create, ticket_update, ticket_delete,
    order_list, order_checkout, order_update, order_delete,
    promotion_list, promotion_create, promotion_update, promotion_delete, promotion_validate,
    artist_create, artist_edit, artist_delete,
    ticket_category_create, ticket_category_edit, ticket_category_delete,)

app_name = 'main'

urlpatterns = [
    path('', home, name='home'),
    # Register
    path('register/', register, name='register'),
    path('register/customer/', register_customer, name='register_customer'),
    path('register/organizer/', register_organizer, name='register_organizer'),
    path('register/admin/', register_admin, name='register_admin'),

    # Login / Logout
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'), 
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/admin/', dashboard_admin, name='dashboard_admin'),
    path('dashboard/organizer/', dashboard_organizer, name='dashboard_organizer'),
    path('dashboard/customer/', dashboard_customer, name='dashboard_customer'),

    # Artist & Profile
    path('artist/', artist_list, name='artist_list'),
    path('artist/create/', artist_create, name='artist_create'),
    path('artist/<str:artist_id>/edit/', artist_edit, name='artist_edit'),
    path('artist/<str:artist_id>/delete/', artist_delete, name='artist_delete'),
    path('profile/customer/', profile_customer, name='profile_customer'),
    path('profile/organizer/', profile_organizer, name='profile_organizer'),
    path('profile/admin/', profile_admin, name='profile_admin'),
    path('profile/admin/update/', profile_admin_update, name='profile_admin_update'),
    path('profile/admin/password/', profile_admin_password, name='profile_admin_password'),
    path('profile/customer/update/', profile_customer_update, name='profile_customer_update'),
    path('profile/customer/password/', profile_customer_password, name='profile_customer_password'),
    path('profile/organizer/update/', profile_organizer_update, name='profile_organizer_update'),
    path('profile/organizer/password/', profile_organizer_password, name='profile_organizer_password'),

    # Venue
    path('venue/', venue_list, name='venue_list'),
    path('venue/create/', venue_create, name='venue_create'),
    path('venue/<uuid:venue_id>/edit/', venue_edit, name='venue_edit'),
    path('venue/<uuid:venue_id>/delete/', venue_delete, name='venue_delete'),

    # Event
    path('event/', event_list, name='event_list'),
    path('event/create/', event_create, name='event_create'),
    path('event/<str:event_id>/edit/', event_edit, name='event_edit'),

    # Ticket Category
    path('ticket-category/', ticket_category_list, name='ticket_category_list'),
    path('ticket-category/create/', ticket_category_create, name='ticket_category_create'),
    path('ticket-category/<str:category_id>/edit/', ticket_category_edit, name='ticket_category_edit'),
    path('ticket-category/<str:category_id>/delete/', ticket_category_delete, name='ticket_category_delete'),

    # Ticket
    path('ticket/customer/', my_tickets, name='my_tickets'),
    path('ticket/admin/', manajemen_tiket_admin, name='manajemen_tiket_admin'),
    path('ticket/organizer/', manajemen_tiket_organizer, name='manajemen_tiket_organizer'),
    path('ticket/create/', ticket_create, name='ticket_create'),
    path('ticket/<str:ticket_id>/update/', ticket_update, name='ticket_update'),
    path('ticket/<str:ticket_id>/delete/', ticket_delete, name='ticket_delete'),

    # Seat
    path('seat/admin/', seat_admin, name='seat_admin'),
    path('seat/organizer/', seat_organizer, name='seat_organizer'),
    path('seat/create/', seat_create, name='seat_create'),       
    path('seat/<str:seat_id>/update/', seat_update, name='seat_update'), 
    path('seat/<str:seat_id>/delete/', seat_delete, name='seat_delete'),

    # Order
    path('order/', order_list, name='order_list'),
    path('order/<uuid:order_id>/update/', order_update, name='order_update'),
    path('order/<uuid:order_id>/delete/', order_delete, name='order_delete'),
    path('order/checkout/<uuid:event_id>/', order_checkout, name='order_checkout'),

    # Promotion
    path('promotion/', promotion_list, name='promotion_list'),
    path('promotion/create/', promotion_create, name='promotion_create'),
    path('promotion/<uuid:promotion_id>/update/', promotion_update, name='promotion_update'),
    path('promotion/<uuid:promotion_id>/delete/', promotion_delete, name='promotion_delete'),
    path('promotion/validate/', promotion_validate, name='promotion_validate'),
]