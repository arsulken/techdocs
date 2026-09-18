from django.urls import path
from . import views
app_name = 'docs'
urlpatterns = [path('', views.projects, name='projects'),
    path('projects/<slug:slug>/', views.project, name='project'),
    path('projects/<slug:project_slug>/<slug:slug>/', views.document, name='document'),
    path('projects/<slug:project_slug>/<slug:slug>/versions/<int:version_id>/', views.document, name='version')]
