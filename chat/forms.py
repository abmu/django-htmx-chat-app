from django import forms
from django.contrib.auth import get_user_model
from .models import Message

User = get_user_model()


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']


class AddForm(forms.Form):
    friend_username = forms.CharField()

    def clean_friend_username(self):
        username = self.cleaned_data['friend_username']
        try:
            self.friend = User.objects.get(username__iexact=username) # __iexact => case insensitive match
        except User.DoesNotExist:
            raise forms.ValidationError('User with this username does not exist')
        return username
    
    def save(self, user):
        user.friends.add(self.friend)