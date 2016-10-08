from django.conf.urls import url
import helium.views as views

urlpatterns = [
    url(r'^grade-scans/([0-9]+)$', views.grade_scans),
    url(r'^grade-scans-redir/$', views.grade_scans_redir),
    url(r'^old-grader/([0-9]+)/$', views.old_grader),
    url(r'^old-grader-redir/$', views.old_grader_redir),
    url(r'^match-exam-scans/([0-9]+)/$', views.match_exam_scans),
    url(r'^match-exam-scans-redir/$', views.match_exam_scans_redir),
    url(r'^old-grader/$', views.old_grader),
    url(r'^progress-problems/$', views.progress_problems),
    url(r'^progress-scans/$', views.progress_scans),
    url(r'^ajax/submit-scan/$', views.ajax_submit_scan), # JSON, for Ajax
    url(r'^ajax/next-scan/$', views.ajax_next_scan),     # JSON, for Ajax
    url(r'^$', views.index),
]
