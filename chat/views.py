from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import MessageForm


@login_required(redirect_field_name=None)
def home(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            print(form.cleaned_data)
            form.save()
            return redirect('chat_home')
    else:
        form = MessageForm()
    
    return render(request, 'chat/home.html', {
        'title': 'Home',
        'form': form
    })