from django.contrib import admin
import helium.models as he

# Register your models here.

# Inline classes, so you can e.g. edit weight
class ProblemInline(admin.TabularInline):
    model = he.Problem
class EvidenceInline(admin.TabularInline):
    model = he.Evidence
class ProblemScribbleInline(admin.TabularInline):
    model = he.ProblemScribble

@admin.register(he.Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color')
    inlines = (ProblemInline,)

@admin.register(he.Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('id', 'test', 'problem_number', 'weight', 'allow_partial')

@admin.register(he.TestScribble)
class TestScribbleAdmin(admin.ModelAdmin):
    list_display = ('id', 'test', 'mathlete', 'team')

@admin.register(he.Verdict)
class VerdictAdmin(admin.ModelAdmin):
    list_display = ('id', 'problem', 'mathlete', 'team', 'cached_score', 'cached_valid')
    inlines = (EvidenceInline, ProblemScribbleInline,)

@admin.register(he.ProblemScribble)
class ProblemScribbleAdmin(admin.ModelAdmin):
    list_display = ('id', 'verdict', 'problem_number', 'testscan')

@admin.register(he.Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ('id', 'verdict', 'user', 'score', 'god_mode')
