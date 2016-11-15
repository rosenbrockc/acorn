from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
import os

def hex_to_RGB(hex):
    ''' "#FFFFFF" -> [255,255,255] '''
    # Pass 16 to the integer function for change of base
    return [int(hex[i:i+2], 16) for i in range(1,6,2)]

def _get_colors(n):
    """Returns n unique and "evenly" spaced colors for the backgrounds
    of the projects.

    Args:
        n (int): The number of unique colors wanted.

    Returns:
        colors (list of str): The colors in hex form.
    """
    # import colorsys
    # HSV_tuples = [(x*1.0/n, 0.5, 0.5) for x in range(n)]
    # RGB_tuples = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples)
    # colors = ['#%02x%02x%02x' % col for col in RGB_tuples]
    # return colors
    # def linear_gradient(start_hex, finish_hex="#FFFFFF", n=10):
    #   ''' returns a gradient list of (n) colors between
    #     two hex colors. start_hex and finish_hex
    #     should be the full six-digit color string,
    #     inlcuding the number sign ("#FFFFFF") '''
    # Starting and ending colors in RGB form
    s = hex_to_RGB('#000000')
    f = hex_to_RGB('#FFFFFF')
    # Initilize a list of the output colors with the starting color
    RGB_list = [s]
    # Calcuate a color at each evenly spaced value of t from 1 to n
    for t in range(1, n):
        # Interpolate RGB vector for color at the current value of t
        curr_vector = [
            int(s[j] + (float(t)/(n-1))*(f[j]-s[j]))
            for j in range(3)
        ]
        # Add it to our list of output colors
        print(tuple(curr_vector))
        RGB_list.append(tuple(curr_vector))
    colors = []
    for col in RGB_list:
        print(col)
        colors.append('#%02x%02x%02x' % (col[0],col[1],col[2]))
    return colors

    
    # max_value = 16581375 #255**3
    # interval = int(max_value / n)
    # colors = [hex(I)[2:].zfill(6) for I in range(0, max_value, interval)]
    # colors = ["#"+i for i in colors]
    # print(colors)
    # return colors
    # from random import randint

    # from math import floor
    # r = lambda
    # # divs = floor(256.0/n)
    # colors = []
    # # this_color = 0
    # while len(colors) < n:
    #     colors.append('#%02X%02X%02X' % (this_color,this_color,this_color))
    #     # this_color += divs

    # return colors

def _make_projcet_list(path):
    """Returns a dictionaries in which each project is a key and the
    tasks are stored as a list within that dictionaly element.
    
    Args:
        path (str): The path to the folder containing the *.json files.
    
    Returns:
        projects (list of dict): A dictionary in which each project is a key 
          containing a list of it's tasks.
    """

    proj = []
    projects = {}
    file_list = os.listdir(path)
    for files in file_list:
        if files.split(".")[0] not in proj and 'json' in files:
            proj.append(files.split(".")[0])

    # get the background color for each project.
    colors = _get_colors(len(proj))
    p_c = 0
    for p in proj:
        tasks = {}
        temp = [x.split(".")[1] for x in file_list if p in x]
        for t in temp:
            tasks[t] = "c"
        tasks["hex_color"] = colors[p_c]
        projects[p] = tasks
        p_c += 1
        
    return projects
        

def index(request):
    context = RequestContext(request)
    projects = request.session.get('projects')
    if not projects:
        path = "/Users/wileymorgan/Dropbox/acorn"
        projects = _make_projcet_list(path)

    
    context_dict = {'projects':projects}
    return render_to_response("ui/index.html", context_dict, context)

def about(request):
    context = RequestContext(request)
    projects = request.session.get('projects')
    if not projects:
        path = "/Users/wileymorgan/Dropbox/acorn"
        projects = _make_projcet_list(path)

    context_dict = {'projects':projects}
    return render_to_response("ui/about.html", context_dict, context)

def dailyLog(request):
    context = RequestContext(request)
    projects = request.session.get('projects')
    if not projects:
        path = "/Users/wileymorgan/Dropbox/acorn"
        projects = _make_projcet_list(path)
    
    context_dict = {'projects':projects}
    return render_to_response("ui/daily_log.html", context_dict, context)
