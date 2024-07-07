from django import forms
from .models import User


class AddForm(forms.Form):
    username = forms.CharField()

    def clean_username(self):
        entered_username = self.cleaned_data['username']
        user = self.initial.get('user')

        try:
            self.friend = User.objects.get(username__iexact=entered_username) # __iexact => case insensitive match
        except User.DoesNotExist:
            raise forms.ValidationError('User with this username does not exist')
        
        if user == self.friend:
            raise forms.ValidationError('You cannot add yourself as a friend')
        
        if self.friend in user.friends_mutual:
            raise forms.ValidationError('You are already friends with this user')
        
        if self.friend in user.get_outgoing_requests():
            raise forms.ValidationError('You have already sent a friend request to this user')

        return entered_username
    
    def save(self, user):
        user.friends.add(self.friend)