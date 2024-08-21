from django import forms
from .models import Message


class MessageForm(forms.ModelForm):
    content = forms.CharField()


    class Meta:
        model = Message
        fields = ['content']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.sender = self.initial.get('sender')
        self.instance.recipient = self.initial.get('recipient')

    def clean_content(self):
        entered_content = self.cleaned_data['content']
        content = entered_content.strip()
        are_friends = self.initial.get('are_friends')

        if not are_friends:
            raise forms.ValidationError('You are not friends with this user')
        
        # No need to manually check for empty content; Django handles this validation automatically
        # if not content:
        #     raise forms.ValidationError('You cannot send empty messages')

        return content