from django.conf.urls import url
from django.urls import path, include
from . import views

urlpatterns = [
    url('lab/vload', views.get_vload, name='vload'),
    url('lab/dep-vload', views.get_dep_vload, name='vload-dep'),
    url('lab/eid', views.get_eid, name='eid'),

    
    url('lab/get/eid', views.pull_eid, name='sync-eid-pull'),
    url('lab/get/vload', views.saveLabs, name='vload-sync')
]
