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
    # role = get_user_role(request.user)
    return render(request, "main/login.html")

def dashboard(request):
    role = request.session.get('role')  # UBAH SESUAI CARA GET ROLE

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