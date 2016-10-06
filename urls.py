from django.conf.urls import url
import helium.views as views

urlpatterns = [
    url(r'^grade-scans', views.grade_scans),
    url(r'^submit-scan', views.submit_scan), # JSON, for Ajax
    url(r'^next-scan', views.next_scan),     # JSON, for Ajax
    url(r'^$', views.index),
]
