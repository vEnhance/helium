from django.contrib import admin
import helium.models as He

# Inline classes, so you can e.g. edit weight
class ProblemInline(admin.TabularInline):
    model = He.Problem
class EvidenceInline(admin.TabularInline):
    model = He.Evidence
class ProblemScribbleInline(admin.TabularInline):
    model = He.ProblemScribble

@admin.register(He.Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color')
    inlines = (ProblemInline,)

@admin.register(He.Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('id', 'test', 'problem_number', 'weight', 'allow_partial')

@admin.register(He.TestScribble)
class TestScribbleAdmin(admin.ModelAdmin):
    list_display = ('id', 'test', 'mathlete', 'team')

@admin.register(He.Verdict)
class VerdictAdmin(admin.ModelAdmin):
    list_display = ('id', 'problem', 'mathlete', 'team', 'score', 'is_valid', 'is_done')
    inlines = (EvidenceInline, ProblemScribbleInline,)

@admin.register(He.ProblemScribble)
class ProblemScribbleAdmin(admin.ModelAdmin):
    list_display = ('id', 'verdict', 'problem_number', 'testscribble')

@admin.register(He.Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ('id', 'verdict', 'user', 'score', 'god_mode')
