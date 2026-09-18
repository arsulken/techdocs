from django.contrib import admin
from .models import Author, Project, Document, Version

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email']
    search_fields = ['full_name', 'email']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_at']
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'created_at']
    list_filter = ['project']
    search_fields = ['title', 'summary']
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ['document', 'number', 'author', 'status', 'published_at']
    list_filter = ['status', 'document__project', 'author']
    search_fields = ['document__title', 'number', 'content']
    autocomplete_fields = ['document', 'author']
    readonly_fields = ['created_at', 'published_at']
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status == Version.Status.PUBLISHED:
            return [f.name for f in Version._meta.fields]
        return self.readonly_fields
    def has_delete_permission(self, request, obj=None):
        return False
