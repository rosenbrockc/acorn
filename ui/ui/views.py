from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext

def index(request):
    context = RequestContext(request)

    context_dict = {}
    return render_to_response("ui/index.html", context_dict, context)

def about(request):
    context = RequestContext(request)

    context_dict = {}
    return render_to_response("ui/about.html", context_dict, context)

def projects(request):
    context = RequestContext(request)

    context_dict = {}
    return render_to_response("ui/projects.html", context_dict, context)

def tasks(request):
    context = RequestContext(request)

    context_dict = {}
    return render_to_response("ui/tasks.html", context_dict, context)

def dailyLog(request):
    context = RequestContext(request)

    context_dict = {}
    return render_to_response("ui/daily_log.html", context_dict, context)
