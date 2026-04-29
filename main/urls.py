from django.urls import path
from main.views import (home, login, logout, register, register_customer, register_organizer, register_admin, 
                        dashboard, dashboard_admin, dashboard_organizer, dashboard_customer, 
                        artist_list,
                        venue_list, venue_create, venue_edit, venue_delete,
                        event_list, event_create, event_edit,
                        ticket_category_list)
                        event_list, event_create, event_edit)
from main.views import login, home, register, register_customer, register_organizer, register_admin, dashboard, dashboard_admin, dashboard_organizer, dashboard_customer, artist_list, ticket_category_list
from main.views import login, register, register_customer, register_organizer, register_admin, dashboard, dashboard_admin, dashboard_organizer, dashboard_customer, artist_list, create_ticket, my_tickets, ticket_list_admin, profile_customer, profile_organizer

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

    #Artist
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

<<<<<<< Updated upstream
    #Ticket Category
    path('ticket-category/', ticket_category_list, name='ticket_category_list'),
=======
    # Ticket
    path('ticket-category/', ticket_category_list, name='ticket_category_list'),
    path('ticket/create/', create_ticket, name='create_ticket'),
    path('my-tickets/', my_tickets, name='my_tickets'),
    path('ticket-list-admin/', ticket_list_admin, name='ticket_list_admin'),
>>>>>>> Stashed changes

    # Order
    # Promotion
]