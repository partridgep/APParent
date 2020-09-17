from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


# signup form for parents
# includes all fields except organization
class ParentSignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required.')
    relationship = forms.CharField(max_length=50, label='Your relationship to the child')
    first_name = forms.CharField(max_length=50, label="First name", help_text='Required.')
    last_name = forms.CharField(max_length=50, label="Last name", help_text='Required.')

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'username', 'relationship', 'password1', 'password2', )

    def __init__(self, is_parent):
        super(ParentSignUpForm, self).__init__()
        self.fields['email'].widget.attrs.update({'autofocus': 'autofocus',
            'required': 'required'})


# signup form for non-parents
# includes organization field
class NotParentSignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required.')
    relationship = forms.CharField(max_length=50, label='Your relationship to the child', help_text='Required.')
    first_name = forms.CharField(max_length=50, label="First name", help_text='Required.')
    last_name = forms.CharField(max_length=50, label="Last name", help_text='Required.')
    organization = forms.CharField(max_length=50, label="Organization")

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'username', 'relationship', 'organization', 'password1', 'password2', )

    def __init__(self, *args):
        super(NotParentSignUpForm, self).__init__()
        self.fields['email'].widget.attrs.update({'autofocus': 'autofocus',
            'required': 'required'})