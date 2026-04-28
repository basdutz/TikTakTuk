from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

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

        # contoh dummy auth
        if username == "admin" and password == "123":
            return redirect("dashboard")
        else:
            return render(request, "login.html", {
                "error": True,
                "message": "Username atau password salah"
            })

    return render(request, "main/login.html")

def logout(request):
    request.session.flush()  # Hapus semua data session
    return redirect('main:login')

def dashboard(request):
    role = request.GET.get('role')  # UBAH SESUAI CARA GET ROLE

    if role == 'admin':
        return redirect('main:dashboard_admin')
    elif role == 'organizer':
        return redirect('main:dashboard_organizer')
    elif role == 'customer':
        return redirect('main:dashboard_customer')
    else:
        return redirect('main:login')

def dashboard_admin(request):
    return render(request, "main/dashboard_admin.html")

def dashboard_organizer(request):
    return render(request, "main/dashboard_organizer.html")

def dashboard_customer(request):
    return render(request, "main/dashboard_customer.html")

@login_required(login_url='main:login')
def artist_list(request):
    return render(request, "main/artist/artist_list.html")

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
