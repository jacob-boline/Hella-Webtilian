from django.shortcuts import render


def index(request):
    return render(request, "locomotive/test.html")


def test2(request):
    return render(request, "locomotive/test2.html")


def burn_test(request):
    return render(request, "locomotive/burn_test.html")


def parallax_test(request):
    return render(request, "locomotive/parallax_test.html")

def pt2(request):
    return render(request, "locomotive/pt2.html")

def pt3(request):
    return render(request, "locomotive/pt3.html")