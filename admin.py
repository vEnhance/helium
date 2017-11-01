"""
HELIUM 2
(c) 2017 Evan Chen
See LICENSE.txt for details.

admin.py

This is fairly straightforward.
It makes the Django admin interface usable, and is amazing.
"""

from django.contrib import admin, auth
import helium as He
from import_export import resources, widgets, fields
from import_export.admin import ImportExportModelAdmin

## INLINE CLASSES, so you can e.g. edit weight
class EntityInline(admin.TabularInline):
	model = He.models.Entity
	# only used to display indivs, so hide shortname, is_team
	fields = ('name', 'team', 'number')
class ProblemInline(admin.TabularInline):
	model = He.models.Problem
	fields = ('problem_number', 'answer', 'weight', 'allow_partial')
class EvidenceInline(admin.TabularInline):
	model = He.models.Evidence
	fields = ('verdict', 'user', 'score', 'god_mode')
	raw_id_fields = ('user',)
class ProblemScribbleInline(admin.TabularInline):
	model = He.models.ProblemScribble
	fields = ('verdict', 'prob_image', 'last_sent_time')
	raw_id_fields = ('verdict',)
class ExamScribbleInline(admin.TabularInline):
	model = He.models.ExamScribble
	fields = ('entity', 'needs_attention',)
	raw_id_fields = ('entity',)

## FILTERS
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
class BadEntityFilter(admin.SimpleListFilter):
	title = "Entities Causing Havoc"
	parameter_name = 'missing'
	def lookups(self, request, model_admin):
		return (("no_verdict", "No Verdicts"),)
	def queryset(self, request, queryset):
		if self.value() is None:
			return queryset
		elif self.value() == "no_verdict":
			return queryset.filter(verdict__isnull=True)

class EntityResource(resources.ModelResource):
	class Meta:
		skip_unchanged = True
		model = He.models.Entity
		fields = ('name', 'shortname', 'id', 'team', 'number', 'is_team')
@admin.register(He.models.Entity)
class EntityAdmin(ImportExportModelAdmin):
	list_display = ('name', 'shortname', 'id', 'team', 'number', 'is_team', 'size')
	inlines = (EntityInline,)
	search_fields = ('name', 'shortname',)
	list_filter = (TeamFilter, BadEntityFilter,)
	resource_class = EntityResource

class ExamResource(resources.ModelResource):
	class Meta:
		skip_unchanged = True
		model = He.models.Exam
		fields = ('name', 'id', 'color', 'is_indiv', 'is_alg_scoring',
				'is_scanned', 'min_grades', 'min_override')
@admin.register(He.models.Exam)
class ExamAdmin(ImportExportModelAdmin):
	list_display = ('name', 'id',  'color', 'is_indiv', 'is_ready', 'is_alg_scoring', 'is_scanned', 'can_upload_scan', 'min_grades', 'min_override')
	inlines = (ProblemInline,)
	search_fields = ('name',)
	list_filter = ('is_indiv', 'is_ready', 'is_alg_scoring', 'is_scanned',)
	resource_class = ExamResource

class ProblemResource(resources.ModelResource):
	exam_name = fields.Field(column_name = 'Exam Name',
			attribute = 'exam',
			widget = widgets.ForeignKeyWidget(He.models.Exam, 'name'))
	class Meta:
		skip_unchanged = True
		model = He.models.Problem
		fields = ('id', 'exam_name', 'problem_number', 'answer', 'weight', 'allow_partial')
@admin.register(He.models.Problem)
class ProblemAdmin(ImportExportModelAdmin):
	list_display = ('id', 'exam', 'problem_number', 'answer', 'weight', 'allow_partial')
	search_fields = ('exam', 'problem_number',)
	list_filter = ('exam__name',)
	resource_class = ProblemResource


class VerdictNoEntityFilter(admin.SimpleListFilter):
	title = "No Name Verdicts"
	parameter_name = 'missing'
	def lookups(self, request, model_admin):
		return (("no_name", "Unmatched Verdicts"), ("inaccessible", "Inaccessible"))
	def queryset(self, request, queryset):
		if self.value() is None:
			return queryset
		elif self.value() == "no_name":
			return queryset.filter(entity__isnull=True, problemscribble__isnull=False)
		elif self.value() == "inaccessible":
			return queryset.filter(entity__isnull=True, problemscribble__isnull=True)

class VerdictResource(resources.ModelResource):
	class Meta:
		skip_unchanged = True
		model = He.models.Verdict
		fields = ('id', 'problem', 'entity', 'score', 'is_valid', 'is_done')
@admin.register(He.models.Verdict)
class VerdictAdmin(ImportExportModelAdmin):
	list_display = ('id', 'problem', 'entity', 'score', 'evidence_count', 'is_valid', 'is_done')
	inlines = (EvidenceInline, ProblemScribbleInline,)
	search_fields = ('problem__exam__name', 'entity__name',)
	list_filter = (VerdictNoEntityFilter, 'problem', 'problem__exam')
	resource_class = VerdictResource
	raw_id_fields = ('entity',)

@admin.register(He.models.EntirePDFScribble)
class EntirePDFAdmin(ImportExportModelAdmin):
	list_display = ('name', 'id', 'is_done', 'exam', 'page_count')
	inlines = (ExamScribbleInline,)
	list_filter = ('is_done', 'exam',)
	search_fields = ('name',)

@admin.register(He.models.ExamScribble)
class ExamScribbleAdmin(ImportExportModelAdmin):
	list_display = ('id', 'exam', 'entity', 'pdf_scribble', 'needs_attention')
	inlines = (ProblemScribbleInline,)
	search_fields = ('entity__name',)
	list_filter = ('exam__name',)
	raw_id_fields = ('entity',)

@admin.register(He.models.ProblemScribble)
class ProblemScribbleAdmin(ImportExportModelAdmin):
	list_display = ('id', 'verdict', 'examscribble', 'last_sent_time')
	search_fields = ('verdict__entity__name',)
	raw_id_fields = ('verdict', 'examscribble',)

class EvidenceResource(resources.ModelResource):
	user_name = fields.Field(column_name = 'User Name',
			attribute = 'user',
			widget = widgets.ForeignKeyWidget(auth.models.User, 'username'))
	class Meta:
		skip_unchanged = True
		model = He.models.Evidence
		fields = ('id', 'verdict', 'user_name', 'score', 'god_mode')
@admin.register(He.models.Evidence)
class EvidenceAdmin(ImportExportModelAdmin):
	list_display = ('id', 'verdict', 'user', 'score', 'god_mode')
	search_fields = ('verdict__entity__name',)
	resource_class = EvidenceResource
	raw_id_fields = ('verdict', 'user',)

class GutsScoreFuncResource(resources.ModelResource):
	class Meta:
		skip_unchanged = True
		model = He.models.GutsScoreFunc
		fields = ('problem_number', 'description', 'answer', 'problem_help_text', 'scoring_function')
@admin.register(He.models.GutsScoreFunc)
class GutsScoreFuncAdmin(ImportExportModelAdmin):
	list_display = ('problem_number', 'description', 'answer', 'problem_help_text')
	search_fields = ('problem_number', 'description',)
	resource_class = GutsScoreFuncResource

@admin.register(He.models.EntityAlpha)
class AlphaAdmin(ImportExportModelAdmin):
	list_display = ('entity', 'cached_alpha', 'id')
	search_fields = ('entity__name',)
	raw_id_fields = ('entity',)

@admin.register(He.models.ScoreRow)
class RowAdmin(ImportExportModelAdmin):
	list_display = ('entity', 'category',  'rank', 'total', 'scores')
	search_fields = ('category', 'entity__name',)
	raw_id_fields = ('entity',)

@admin.register(He.models.ThreadTaskRecord)
class ThreadTaskAdmin(ImportExportModelAdmin):
	list_display = ('id', 'name', 'user', 'status', 'time_created', 'last_updated', 'output',)
	search_fields = ('name', 'output',)
	raw_id_fields = ('user',)
