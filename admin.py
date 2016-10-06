from django.contrib import admin
import helium as He

# Inline classes, so you can e.g. edit weight
class ProblemInline(admin.TabularInline):
    model = He.models.Problem
class EvidenceInline(admin.TabularInline):
    model = He.models.Evidence
class ProblemScribbleInline(admin.TabularInline):
    model = He.models.ProblemScribble

@admin.register(He.models.Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'id',  'color', 'is_alg_scoring', 'is_ready')
    inlines = (ProblemInline,)

@admin.register(He.models.Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'exam', 'problem_number', 'id',  'weight', 'allow_partial')

@admin.register(He.models.ExamScribble)
class ExamScribbleAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'exam', 'mathlete', 'team', 'id')

@admin.register(He.models.Verdict)
class VerdictAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'id', 'problem', 'mathlete', 'team', 'score', 'is_valid', 'is_done')
    inlines = (EvidenceInline, ProblemScribbleInline,)

@admin.register(He.models.ProblemScribble)
class ProblemScribbleAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'id', 'verdict', 'examscribble')

@admin.register(He.models.Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ('id', 'verdict', 'user', 'score', 'god_mode')
