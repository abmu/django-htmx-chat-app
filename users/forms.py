import re
from django import forms
from django.contrib.auth import authenticate
from allauth.account.forms import SignupForm
from .models import User


class UserSignupForm(SignupForm):
    def clean_username(self):
        username = super().clean_username()

        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise forms.ValidationError('Username can only contain letters, digits, and underscores')

        if User.has_deleted_user_prefix(username):
            raise forms.ValidationError(f'Username cannot start with \'{User.DELETED_USER_PREFIX}\'')
        
        return username

class AddFriendForm(forms.Form):
    username = forms.CharField()

    def clean_username(self):
        entered_username = self.cleaned_data['username']
        self.user = self.initial.get('user')

        try:
            self.friend = User.objects.get(username__iexact=entered_username) # __iexact => case insensitive match
        except User.DoesNotExist:
            raise forms.ValidationError('User with this username does not exist')
        
        if not self.friend.is_active:
            raise forms.ValidationError('You cannot add inactive accounts')

        if self.user == self.friend:
            raise forms.ValidationError('You cannot add yourself as a friend')
        
        if self.user.has_friend_mutual(self.friend):
            raise forms.ValidationError('You are already friends with this user')
        
        if self.user.has_outgoing_request_to(self.friend):
            raise forms.ValidationError('You have already sent a friend request to this user')

        return entered_username
    
    def save(self):
        self.user.add_friend(self.friend)


class DeleteAccountForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

    def clean_password(self):
        entered_password = self.cleaned_data['password']
        user = self.initial.get('user')

        if not authenticate(username=user.username, password=entered_password):
            raise forms.ValidationError('Incorrect password entered')
        
        return entered_password