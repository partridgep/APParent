from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
# from .forms import SignUpForm
from django.contrib.auth.decorators import login_required

# Create your views here.

def home(request):
    return redirect('index')

def signup(request, is_parent):
    # is_parent = is_parent
    # print(is_parent)
    return render(request, 'registration/signup.html'
    , {'is_parent': is_parent}
     )

def register_user(request):
    if request.method == "POST":
        print("hitting submit")
        parent_checked = request.POST.get('parent_check')
        if parent_checked == 'on':
            print("is checked")
            is_parent = True
        else:
            print("not checked")
            is_parent = False

        #redirect to signup form
        return redirect('signup', 
        is_parent=is_parent
        )

    return render(request, 'register_user.html')

@login_required
def children_index(request):
    pass

