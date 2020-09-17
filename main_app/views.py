from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from .forms import ParentSignUpForm, NotParentSignUpForm
from django.contrib.auth.decorators import login_required

# Create your views here.

def home(request):
    return redirect('index')

def signup(request, is_parent):
    error_message = ''

    if request.method == 'POST':
        print(request.POST)
        if is_parent == 1:
            form = ParentSignUpForm(request.POST)
        else:
            form = NotParentSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('index')
        else:
            error_message = 'Invalid sign up, try again!'
    
    if is_parent == 1:
        form = ParentSignUpForm()
    else:
        form = NotParentSignUpForm()
    context = {'is_parent': is_parent, 'form': form, 'error_message': error_message}
    return render(request, 'registration/signup.html', context)

def register_user(request):
    if request.method == "POST":
        print("hitting submit")
        parent_checked = request.POST.get('parent_check')
        if parent_checked == 'on':
            print("is checked")
            is_parent = 1
        else:
            print("not checked")
            is_parent = 0

        #redirect to signup form
        return redirect('signup', is_parent=is_parent)

    return render(request, 'register_user.html')

@login_required
def children_index(request):
    return render(request, 'children/index.html')

