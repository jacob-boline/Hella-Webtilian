from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib.admin.views.decorators import user_passes_test
from hr_access.models import User
from hr_access.forms import StaffForm
import json


class AdminLogin(LoginView):
    template_name = 'hr_access/loginview_form.html'


@user_passes_test(lambda u: u.is_superuser)
def add_staff(request):
    if request.method == 'POST':
        form = StaffForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = User.objects.create(username=data['username'], email=data['email'], is_staff=True).save(commit=False)
            user.set_password(password=data['password1'])
            user.save()
            headers_dict = {'dialogChanged': None,
                            'showMessage': f'{messages.get_messages(request)}'}
            return HttpResponse(status=204, headers={'HX-Trigger': json.dumps(headers_dict)})
    else:
        form = StaffForm()
    return render(request, 'hr_access/add_staff_form.html', {'add_staff_form': form})


def access_panel(request):
    return render(request, 'hr_access/access_panel.html')


def user_panel(request):
    # headers_dict = {'accessChanged': None}
    response = render(request, 'hr_access/user_panel.html')
    # response.headers['HX-Trigger'] = json.dumps(headers_dict)
    return response


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request=request, username=username, password=password)
        if user is not None:
            login(request, user)
            headers_dict = {'dialogChanged': None,
                            'bulletinChanged': None,
                            'accessChanged': None,
                            'showsChanged': None,
                            'showMessage': 'login successful'}
            return HttpResponse(status=204, headers={'HX-Trigger': json.dumps(headers_dict)})
        else:
            form = AuthenticationForm(request.POST)
            messages.info(request, 'No match found for Username/Password')
            headers_dict = {'showMessage': 'No match found for Username/Password'}
            response = render(request, 'hr_access/login.html', {'authentication_form': form})
            response.headers['HX-Trigger'] = json.dumps(headers_dict)
    else:
        form = AuthenticationForm()
        response = render(request, 'hr_access/login.html', {'authentication_form': form})
    return response


def login_success(request):
    return render(request, 'hr_access/login_success.html')


def user_logout(request):
    logout(request)


def logout_redirect(request):
    headers_dict = {'accessChanged': None,
                    'bulletinChanged': None,
                    'dialogChanged': None,
                    'showsChanged': None,
                    'showMessage': 'You have been logged out.'}
    return HttpResponse(status=204, headers={'HX-Trigger': json.dumps(headers_dict)})


@login_required
def password_change(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)

    else:
        form = PasswordChangeForm(user=request.user)
        return render(request, 'hr_access/password_change_form.html', {'form': form})


def sidebar_access(request):
    return render(request, 'hr_access/_sidebar_ul.html')
