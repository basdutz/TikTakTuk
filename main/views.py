from django.shortcuts import render, redirect

def _resolve_role(request):
    return request.GET.get('role') or request.session.get('role')
 
 
def _resolve_organizer_id(request, role):
    org_id = request.session.get('organizer_id')
    if role == 'organizer' and not org_id:
        org_id = '3b9c1e2a-5d4f-4c8e-9a1b-2f3d4e5f6a7b'
    return org_id

def _ctx(request, **extra):
    role = _resolve_role(request)
    base = {
        'role': role,
        'username': request.session.get('username'),
        'organizer_id': _resolve_organizer_id(request, role),
        'is_admin': role == 'admin',
        'is_organizer': role == 'organizer',
        'is_customer': role == 'customer',
    }
    base.update(extra)
    return base
 
 
def _require_manage(request):
    return _resolve_role(request) in ('admin', 'organizer')

def home(request):
    return render(request, "main/home.html")

def register(request):
    return render(request, "main/register_role.html")

def register_customer(request):
    return render(request, "main/register_customer.html")

def register_organizer(request):
    return render(request, "main/register_organizer.html")

def register_admin(request):
    return render(request, "main/register_admin.html")

def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if username == "admin" and password == "123":
            request.session['role'] = 'admin'
            request.session['username'] = 'admin'
            return redirect("main:dashboard_admin")
        elif username == "organizer" and password == "123":
            request.session['role'] = 'organizer'
            request.session['username'] = 'organizer'
            request.session['organizer_id'] = '550e8400-e29b-41d4-a716-446655440000'
            return redirect("main:dashboard_organizer")
        elif username == "customer" and password == "123":
            request.session['role'] = 'customer'
            request.session['username'] = 'customer'
            return redirect("main:dashboard_customer")
        else:
            return render(request, "main/login.html", {
                "error": True,
                "message": "Username atau password salah",
            })
 
    return render(request, "main/login.html")
 
 
def logout(request):
    request.session.flush()
    return redirect('main:home')

def dashboard(request):
    role = request.GET.get('role') or request.session.get('role')
 
    if role == 'admin':
        return redirect('main:dashboard_admin')
    elif role == 'organizer':
        return redirect('main:dashboard_organizer')
    elif role == 'customer':
        return redirect('main:dashboard_customer')
    return redirect('main:home')
 
 
def dashboard_admin(request):
    return render(request, "main/dashboard_admin.html", _ctx(request, role='admin'))
 
 
def dashboard_organizer(request):
    return render(request, "main/dashboard_organizer.html", _ctx(request, role='organizer'))
 
 
def dashboard_customer(request):
    return render(request, "main/dashboard_customer.html", _ctx(request, role='customer'))


def profile(request):
    role = request.GET.get('role')

    if role == 'organizer':
        return redirect('main:profile_organizer')
    elif role == 'customer':
        return redirect('main:profile_customer')
    else:
        return redirect('main:home')
    
def profile_organizer(request):
    return render(request, "main/profile_organizer.html", {'role': 'organizer', 'username': 'organizer'})

def profile_customer(request):
    return render(request, "main/profile_customer.html", {'role': 'customer', 'username': 'customer'})

def artist_list(request):
    return render(request, "main/artist/artist_list.html", _ctx(request))

# Venue Views
def venue_list(request):
    return render(request, "main/venue/venue_list.html", _ctx(request))

def venue_create(request):
    # Spec: pakai modal di halaman list. Lempar balik ke list.
    if not _require_manage(request):
        return redirect('main:venue_list')
    return redirect('main:venue_list')

def venue_edit(request, venue_id):
    if not _require_manage(request):
        return redirect('main:venue_list')
    return redirect('main:venue_list')

def venue_delete(request, venue_id):
    if not _require_manage(request):
        return redirect('main:venue_list')
    return redirect('main:venue_list')

# Event Views
def event_list(request):
    return render(request, "main/event/event_list.html", _ctx(request))

def event_create(request):
    if not _require_manage(request):
        return redirect('main:event_list')
    return render(request, "main/event/event_form.html", _ctx(
        request,
        is_edit=False,
    ))

def event_edit(request, event_id):
    if not _require_manage(request):
        return redirect('main:event_list')
    return render(request, "main/event/event_form.html", _ctx(
        request,
        is_edit=True,
        event_id=event_id,
    ))

def ticket_category_list(request):
    return render(request, 'main/ticket_category/category_list.html', _ctx(request))

def my_tickets(request):
    return render(request, "main/ticket/my_tickets.html", {'role': 'customer', 'username': 'customer'})

def manajemen_tiket_admin(request):
    return render(request, "main/ticket/manajemen_tiket.html", {'role': 'admin', 'username': 'admin'})

def manajemen_tiket_organizer(request):
    return render(request, "main/ticket/manajemen_tiket.html", {'role': 'organizer', 'username': 'organizer'})

def seat_admin(request):
    return render(request, 'main/seat/seat.html', {'role': 'admin', 'username': 'admin'})

def seat_organizer(request):
    return render(request, 'main/seat/seat.html', {'role': 'organizer', 'username': 'organizer'})

# Order Views
def order_list_admin(request):
    return render(request, 'main/order/order_list.html', {'role': 'admin', 'username': 'admin'})

def order_list_organizer(request):
    return render(request, 'main/order/order_list.html', {'role': 'organizer', 'username': 'organizer'})

def order_list_customer(request):
    return render(request, 'main/order/order_list.html', {'role': 'customer', 'username': 'customer'})

def order_checkout(request, event_id):
    return render(request, 'main/order/order_checkout.html', {
        'role': 'customer',
        'username': 'customer',
        'event_id': event_id,
    })

# Promotion Views
def promotion_list_admin(request):
    return render(request, 'main/promotion/promotion_list.html', {'role': 'admin', 'username': 'admin'})

def promotion_list_organizer(request):
    return render(request, 'main/promotion/promotion_list.html', {'role': 'organizer', 'username': 'organizer'})

def promotion_list_customer(request):
    return render(request, 'main/promotion/promotion_list.html', {'role': 'customer', 'username': 'customer'})
