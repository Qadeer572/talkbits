from django.http import HttpResponse
from django.shortcuts import render

def index(request):
    return render(request, 'index.html')


def home2(request):
    return render(request,'index.html')