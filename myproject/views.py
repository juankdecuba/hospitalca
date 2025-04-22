from django.shortcuts import render

def index(request):
    return render(request,'index.html',{})

def login(request):
    return render(request,'login.html',{})

def profile(request):
    return render(request,'profile.html',{})

def testimonials(request):
    return render(request,'testimonials.html',{})

def register(request):
    return render(request,'register.html',{})

def reserve(request):
    return render(request,'reserve.html',{})
    