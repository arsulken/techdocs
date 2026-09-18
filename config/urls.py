from django.contrib import admin
from django.urls import include, path
urlpatterns = [path('admin/', admin.site.urls), path('', include('docs.urls'))]
admin.site.site_header = 'Техническая документация'
admin.site.site_title = 'Управление документацией'
admin.site.index_title = 'Проекты, документы, версии и авторы'
