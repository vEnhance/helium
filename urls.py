"""
HELIUM 2
(c) 2017 Evan Chen
See LICENSE.txt for details.

urls.py

Pretty self-explanatory.

CONVENTION: Name of view function is always the URL
with all dashes and slashes replaced by underscores
The corresponding template, if applicable, uses the URL name
"""

from django.conf.urls import url
import helium.views as views
urlpatterns = [
	url(r'^grade-scans/([0-9]+)/$', views.grade_scans),
	url(r'^grade-scans/redir/$', views.grade_scans_redir),
	url(r'^old-grader/exam/([0-9]+)/$', views.old_grader_exam),
	url(r'^old-grader/exam/redir/$', views.old_grader_exam_redir),
	url(r'^old-grader/problem/([0-9]+)/$', views.old_grader_problem),
	url(r'^old-grader/problem/redir/$', views.old_grader_problem_redir),
	url(r'^fast-match/([0-9]+)/$', views.fast_match),
	url(r'^fast-match/redir/$', views.fast_match_redir),
	url(r'^fast-match/([0-9]+)/(attention)/$', views.fast_match),
	url(r'^fast-match/redir/(attention)/$', views.fast_match_redir),
	url(r'^view-verdict/([0-9]+)/$', views.view_verdict),
	url(r'^view-conflicts/all/$', views.view_conflicts_all),
	url(r'^view-conflicts/own/$', views.view_conflicts_own),
	url(r'^find-paper/$', views.find_paper),
	url(r'^view-paper/scan/([0-9]+)/$', views.view_paper),
	url(r'^view-paper/([0-9]+)/([0-9]+)/$', views.view_paper),
	url(r'^estimation-calc/$', views.estimation_calc),
	url(r'^upload-scans/$', views.upload_scans),
	url(r'^view-pdf/([0-9]+)/$', views.view_pdf),
	url(r'^view-pdf/redir/$', views.view_pdf_redir),
	url(r'^view-task/([0-9]+)/$', views.view_task),
	url(r'^progress-problems/$', views.progress_problems),
	url(r'^progress-scans/$', views.progress_scans),
	url(r'^ajax/submit-scan/$', views.ajax_submit_scan),
	url(r'^ajax/next-scan/$', views.ajax_next_scan),
	url(r'^ajax/prev-evidence/$', views.ajax_prev_evidence),
	url(r'^ajax/submit-match/$', views.ajax_submit_match),
	url(r'^ajax/next-match/$', views.ajax_next_match),
	url(r'^ajax/task-query/$', views.ajax_task_query),
	url(r'^reports/short/$', views.reports_short),
	url(r'^reports/extended/$', views.reports_extended),
	url(r'^reports/full/$', views.reports_full), # super-user only
	url(r'^reports/teaser/$', views.reports_teaser), # public
	url(r'^reports/spreadsheet/$', views.reports_spreadsheet), # super-user only
	url(r'^reports/awards/$', views.reports_awards),
	url(r'^management/([a-zA-Z]+)/$', views.run_management),
	url(r'^$', views.index),
]
# TODO: should really use URL patterns here, sorry
# didn't know they existed back when I wrote this thing
