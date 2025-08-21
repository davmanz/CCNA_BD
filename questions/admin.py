from django.contrib import admin
from .models import SingleChoiceQuestion, MultipleChoiceQuestion, DragAndDropQuestion

class SingleChoiceQuestionAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'answer', 'has_image', 'image_filename')
    list_filter = ('has_image',)
    search_fields = ('text', 'image_filename')
    
    def text_preview(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Pregunta'

class MultipleChoiceQuestionAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'answer', 'has_image', 'image_filename')
    list_filter = ('has_image',)
    search_fields = ('text', 'image_filename')
    
    def text_preview(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Pregunta'

class DragAndDropQuestionAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'has_image', 'image_filename')
    list_filter = ('has_image',)
    search_fields = ('text', 'image_filename')
    
    def text_preview(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Pregunta'

admin.site.register(SingleChoiceQuestion, SingleChoiceQuestionAdmin)
admin.site.register(MultipleChoiceQuestion, MultipleChoiceQuestionAdmin)
admin.site.register(DragAndDropQuestion, DragAndDropQuestionAdmin)