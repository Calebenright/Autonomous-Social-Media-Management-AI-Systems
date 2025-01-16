from django.shortcuts import render

def products(request):
    return render(request, 'products.html')

def thank_you(request):
    return render(request, 'thank_you.html')

def item1(request):
    return render(request, 'item1.html')

def item2(request):
    return render(request, 'item2.html')