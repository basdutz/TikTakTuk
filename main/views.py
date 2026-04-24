from django.shortcuts import render

def show_main(request):
    return render(request, "main/register_role.html")

def register_customer(request):
    return render(request, "main/register_customer.html")

def register_organizer(request):
    return render(request, "main/register_organizer.html")

def login(request):
    role = get_user_role(request.user)
    return render(request, "main/login.html")
