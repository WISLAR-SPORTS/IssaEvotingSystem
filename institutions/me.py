
from django.db import models
from django.shortcuts import HTTPResponse
from django.urls import path
"""

def home(request):
    student=students.object.all()
    output = ""
    for s in students: 
        output += s.name + "-" + s.course
    return HTTPResponse(output)
class students(models.model):
    name=models.CharField(max_length=200)
    course=models.CharField(max_length=300)

app_name = "me"

urlpatterns = [
    path('', home, name="home"),
]

"""