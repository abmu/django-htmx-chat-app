from django import forms
from django.contrib.auth import authenticate
from .models import User


class AddFriendForm(forms.Form):
    username = forms.CharField()

    def clean_username(self):
        entered_username = self.cleaned_data['username']
        self.user = self.initial.get('user')

        try:
            self.friend = User.objects.get(username__iexact=entered_username) # __iexact => case insensitive match
        except User.DoesNotExist:
            raise forms.ValidationError('User with this username does not exist')
        
        if self.user == self.friend:
            raise forms.ValidationError('You cannot add yourself as a friend')
        
        if self.friend in self.user.friends_mutual:
            raise forms.ValidationError('You are already friends with this user')
        
        if self.friend in self.user.get_outgoing_requests():
            raise forms.ValidationError('You have already sent a friend request to this user')

        return entered_username
    
    def save(self):
        self.user.friends.add(self.friend)


class DeleteAccountForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_password(self):
        entered_password = self.cleaned_data['password']
        user = self.initial.get('user')

        if not authenticate(username=user.username, password=entered_password):
            raise forms.ValidationError('Incorrect password entered')
        
        return entered_password