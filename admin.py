"""
HELIUM
(c) 2016 Evan Chen
See LICENSE.txt for details.

admin.py

This is fairly straightforward.
It makes the Django admin interface usable, and is amazing.
"""

from django.contrib import admin
import helium as He

# Inline classes, so you can e.g. edit weight
class EntityInline(admin.TabularInline):
	model = He.models.Entity
	# only used to display indivs, so hide shortname, is_team
	fields = ('name', 'number') 
class ProblemInline(admin.TabularInline):
	model = He.models.Problem
	fields = ('problem_number', 'answer', 'weight', 'allow_partial')
class EvidenceInline(admin.TabularInline):
	model = He.models.Evidence
	fields = ('verdict', 'user', 'score', 'god_mode')
class ProblemScribbleInline(admin.TabularInline):
	model = He.models.ProblemScribble
	fields = ('verdict', 'prob_image', 'most_recent_grab')


class TeamFilter(admin.SimpleListFilter):
	title = "Individual vs Team"
	parameter_name = 'type'
	def lookups(self, request, model_admin):
		return (("indiv", "Individual"), ("team", "Team"),)
	def queryset(self, request, queryset):
		if self.value() is None:
			return queryset
		elif self.value() == "indiv":
			return queryset.filter(is_team=False)
		elif self.value() == "team":
			return queryset.filter(is_team=True)

@admin.register(He.models.Entity)
class EntityAdmin(admin.ModelAdmin):
	list_display = ('name', 'id', 'team', 'number', 'is_team')
	list_filter = (TeamFilter,)
	inlines = (EntityInline,)

@admin.register(He.models.Exam)
class ExamAdmin(admin.ModelAdmin):
	list_display = ('name', 'id',  'color', 'is_alg_scoring', 'is_ready', 'min_grades', 'min_override')
	inlines = (ProblemInline,)

@admin.register(He.models.Problem)
class ProblemAdmin(admin.ModelAdmin):
	list_display = ('id', 'exam', 'problem_number', 'weight', 'allow_partial')

@admin.register(He.models.ExamScribble)
class ExamScribbleAdmin(admin.ModelAdmin):
	list_display = ('id', 'exam', 'entity')
	inlines = (ProblemScribbleInline,)

@admin.register(He.models.Verdict)
class VerdictAdmin(admin.ModelAdmin):
	list_display = ('id', 'problem', 'entity', 'score', 'evidence_count', 'is_valid', 'is_done')
	inlines = (EvidenceInline, ProblemScribbleInline,)

@admin.register(He.models.ProblemScribble)
class ProblemScribbleAdmin(admin.ModelAdmin):
	list_display = ('id', 'verdict', 'examscribble', 'last_sent_time')

@admin.register(He.models.Evidence)
class EvidenceAdmin(admin.ModelAdmin):
	list_display = ('id', 'verdict', 'user', 'score', 'god_mode')

@admin.register(He.models.EntityAlpha)
class AlphaAdmin(admin.ModelAdmin):
	list_display = ('entity', 'cached_alpha', 'id')

@admin.register(He.models.GutsScoreFunc)
class GutsScoreFuncAdmin(admin.ModelAdmin):
	list_display = ('problem_number', 'description', 'answer', 'problem_help_text')

@admin.register(He.models.EntirePDFScribble)
class EntirePDFAdmin(admin.ModelAdmin):
	list_display = ('name', 'is_done')
