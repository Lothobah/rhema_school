from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from great_alliance_portal.EmailBackEnd import EmailBackEnd
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth import views as auth_views
from django.contrib import messages


def home(request):
    return render(request, "login_page.html")


def web_home(request):
    return render(request, "website_templates/homepage.html")
#def show_login(request):
    #return render(request, "show_login.html")


def DoLogin(request):
    try:
        if request.method != "POST":
            messages.error(request, "Invalid Login Details")
            return HttpResponseRedirect("/")
            #return HttpResponse("<h3>This account was deleted<h3/>")
        else:
            user = EmailBackEnd.authenticate(request, username=request.POST.get(
                "username"), password=request.POST.get("password"))  # email
            if user != None:
                login(request, user)
                if user.user_type == "1":
                    return HttpResponseRedirect("/admin_homepage")
                elif user.user_type == "2":
                    return HttpResponseRedirect(reverse("staff_homepage"))
                elif user.user_type == "4":
                    return HttpResponseRedirect(reverse("bursar_homepage"))
                else:
                    return HttpResponseRedirect(reverse("student_homepage"))

            else:
                messages.error(
                    request, 'Your Username or Password is incorrect.')
                return HttpResponseRedirect("/")
    except:
        return HttpResponseRedirect("/")


def Logout_User(request):
    logout(request)
    messages.success(request, "You have successfully logged out.")
    return HttpResponseRedirect("/")
