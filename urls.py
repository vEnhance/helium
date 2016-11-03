"""
HELIUM
(c) 2016 Evan Chen
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
	url(r'^match-papers/([0-9]+)/$', views.match_papers),
	url(r'^match-papers/redir/$', views.match_papers_redir),
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
	url(r'^progress-problems/$', views.progress_problems),
	url(r'^progress-scans/$', views.progress_scans),
	url(r'^ajax/submit-scan/$', views.ajax_submit_scan), 
	url(r'^ajax/next-scan/$', views.ajax_next_scan),
	url(r'^ajax/prev-evidence/$', views.ajax_prev_evidence),
	url(r'^reports/short/$', views.reports_short),
	url(r'^reports/extended/$', views.reports_extended),
	url(r'^reports/full/$', views.reports_full), # super-user only
	url(r'^reports/teaser/$', views.teaser),
	url(r'^spreadsheet/$', views.spreadsheet),
	url(r'^management/([a-zA-Z]+)/$', views.run_management),
	url(r'^$', views.index),
]
