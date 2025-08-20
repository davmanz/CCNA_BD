from django.contrib import admin
from .models import SingleChoiceQuestion, MultipleChoiceQuestion, DragAndDropQuestion

class SingleChoiceQuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'answer')

class MultipleChoiceQuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'answer')

class DragAndDropQuestionAdmin(admin.ModelAdmin):
    list_display = ('text',)

admin.site.register(SingleChoiceQuestion, SingleChoiceQuestionAdmin)
admin.site.register(MultipleChoiceQuestion, MultipleChoiceQuestionAdmin)
admin.site.register(DragAndDropQuestion, DragAndDropQuestionAdmin)
