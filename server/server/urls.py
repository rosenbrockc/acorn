"""ui URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from ui import views
from django.conf import settings
from django.contrib.staticfiles.views import serve as serve_static
from django.views.decorators.cache import never_cache

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', views.index,name="index"),
    url(r'^about/$',views.about,name="about"),
    url(r'^daily_log/$',views.dailyLog,name="daily_log"),
    url(r'^nav/$',views.nav,name="nav"),
    url(r'^sub_nav/$',views.sub_nav,name="sub_nav"),
    url(r'^sub_nav_list/$',views.sub_nav_list,name="sub_nav_list"),
    url(r'^view_proj/$',views.view_proj,name="view_proj"),
    url(r'^view_tasks/$',views.view_tasks,name="view_tasks"),
    url(r'^day_table/$',views.day_table,name="day_table"),
    url(r'^detail_table/$',views.detail_table,name="detail_table"),
    url(r'^static/(?P<path>.*)$', never_cache(serve_static)),    
 ]
