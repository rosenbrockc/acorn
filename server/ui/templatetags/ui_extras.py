from django import template

register = template.Library()

@register.filter(name='getcolor')
def getcolor(d,key):
    return d[key][0]

@register.filter(name='getdir')
def getdir(d,key):
    return d[key][1]
