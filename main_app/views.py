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

def parent_signup(request):
    error_message = ''

    # if submitting the form
    if request.method == 'POST':
        print(request.POST)
        # submit the parent form
        form = ParentSignUpForm(request.POST)

        # authenticate and login new user if valid
        if form.is_valid():
            print("form is valid")
            user = form.save()
            user.refresh_from_db()
            user.profile.is_parent = True
            user.profile.relationship = form.cleaned_data.get('relationship')
            user.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            # redirect to children login page
            return redirect('index')
        else:
            error_message = 'Invalid sign up, try again!'
    
    # present form
    form = ParentSignUpForm()
    # provide context for rendering page
    context = {'form': form, 'error_message': error_message}
    return render(request, 'registration/parent_signup.html', context)



def nonparent_signup(request):
    error_message = ''
    # if submitting the form
    if request.method == 'POST':
        print(request.POST)
        # submit the parent form
        form = NotParentSignUpForm(request.POST)
        print(form.errors)
        # authenticate and login new user if valid
        if form.is_valid():
            print("form is valid")
            user = form.save()
            user.refresh_from_db()
            user.profile.is_parent = False
            user.profile.relationship = form.cleaned_data.get('relationship')
            user.profile.organization = form.cleaned_data.get('organization')
            user.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            # redirect to children login page
            return redirect('index')
        else:
            error_message = 'Invalid sign up, try again!'
    
    # present form
    form = NotParentSignUpForm()
    # provide context for rendering page
    context = {'form': form, 'error_message': error_message}
    return render(request, 'registration/nonparent_signup.html', context)

def register_user(request):
    #if submitting form
    if request.method == "POST":
        # check if checkbox is checked
        parent_checked = request.POST.get('parent_check')
        # if so, user is parent
        if parent_checked == 'on':
            #redirect to signup form
            return redirect('parent_signup')
            is_parent = 1
        else:
            return redirect('nonparent_signup')
            is_parent = 0


    return render(request, 'register_user.html')

@login_required
def children_index(request):
    user = request.user
    print(user.profile)
    if (user.profile.is_parent):
        print("User is parent")
    else:
        print("user is not parent")
    return render(request, 'children/index.html')

