from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

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
            return redirect("main:dashboard_organizer")
        elif username == "customer" and password == "123":
            request.session['role'] = 'customer'
            request.session['username'] = 'customer'
            return redirect("main:dashboard_customer")
        else:
            return render(request, "main/login.html", {
                "error": True,
                "message": "Username atau password salah"
            })

    return render(request, "main/login.html")

def logout(request):
    request.session.flush() 
    return redirect('main:home')

def dashboard(request):
    role = request.GET.get('role')

    if role == 'admin':
        return redirect('main:dashboard_admin')
    elif role == 'organizer':
        return redirect('main:dashboard_organizer')
    elif role == 'customer':
        return redirect('main:dashboard_customer')
    else:
        return redirect('main:home')

def dashboard_admin(request):
    return render(request, "main/dashboard_admin.html", {
        'role': request.session.get('role', 'admin'),
        'username': request.session.get('username', 'admin'),
    })

def dashboard_organizer(request):
    return render(request, "main/dashboard_organizer.html", {'role': 'organizer', 'username': 'organizer'})

def dashboard_customer(request):
    return render(request, "main/dashboard_customer.html", {'role': 'customer', 'username': 'customer'})

def artist_list(request):
    role = request.GET.get('role', '')
    return render(request, "main/artist/artist_list.html", {
        'is_admin': role == 'admin',
        'role': role,
        'username': request.session.get('username', ''),
    })

def venue_list(request):
    return render(request, "main/venue/venue_list.html")

def venue_create(request):
    return render(request, "main/venue/venue_form.html")

def venue_edit(request, venue_id):
    return render(request, "main/venue/venue_form.html", {'venue_id': venue_id})

def venue_delete(request, venue_id):
    return render(request, "main/venue/venue_confirm_delete.html", {'venue_id': venue_id})

def event_list(request):
    return render(request, "main/event/event_list.html")

def event_create(request):
    return render(request, "main/event/event_form.html")

def event_edit(request, event_id):
    return render(request, "main/event/event_form.html", 
                  {'event_id': event_id})

def ticket_category_list(request):
    role = request.GET.get('role')
    return render(request, 'main/ticket_category/category_list.html', {
        'role': role,
        'is_admin': role == 'admin',
        'is_organizer': role == 'organizer'
    })
