from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required(redirect_field_name=None)
def home(request):
    return render(request, 'chat/home.html')