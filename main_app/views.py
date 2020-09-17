from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from .forms import ParentSignUpForm, NotParentSignUpForm
from django.contrib.auth.decorators import login_required

# Create your views here.

def home(request):
    # redirect to children index on intitial load
    # if user is not logged in, they will be redirected to login page
    return redirect('index')

def signup(request, is_parent):
    error_message = ''

    # if submitting the form
    if request.method == 'POST':
        print(request.POST)
        # if is parent
        if is_parent == 1:
            # submit the parent form
            form = ParentSignUpForm(request.POST)
        else:
            # else submit the non-parent form
            form = NotParentSignUpForm(request.POST)
        # authenticate and login new user if valid
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            # redirect to children login page
            return redirect('index')
        else:
            error_message = 'Invalid sign up, try again!'
    
    # present form according to is_parent value
    if is_parent == 1:
        form = ParentSignUpForm()
    else:
        form = NotParentSignUpForm()

    # provide context for rendering page
    context = {'is_parent': is_parent, 'form': form, 'error_message': error_message}
    return render(request, 'registration/signup.html', context)

def register_user(request):
    #if submitting form
    if request.method == "POST":
        # check if checkbox is checked
        parent_checked = request.POST.get('parent_check')
        # if so, user is parent
        if parent_checked == 'on':
            is_parent = 1
        else:
            is_parent = 0

        #redirect to signup form
        return redirect('signup', is_parent=is_parent)

    return render(request, 'register_user.html')

@login_required
def children_index(request):
    return render(request, 'children/index.html')

