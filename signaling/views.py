# Create your views here.
from django.shortcuts import render

def call_page(request):
    return render(request, 'test.html')
