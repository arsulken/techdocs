from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from .models import Project, Document, Version, Author

def projects(request):
    items = Project.objects.annotate(document_count=Count('documents', distinct=True,
        filter=Q(documents__versions__status=Version.Status.PUBLISHED)))
    return render(request, 'docs/projects.html', {'projects': items,
        'document_count': Document.objects.filter(versions__status='published').distinct().count(),
        'version_count': Version.objects.filter(status='published').count(),
        'author_count': Author.objects.count()})

def project(request, slug):
    item = get_object_or_404(Project, slug=slug)
    query = request.GET.get('q', '').strip()
    documents = item.documents.filter(versions__status='published').distinct()
    if query:
        documents = documents.filter(Q(title__icontains=query) | Q(summary__icontains=query))
    return render(request, 'docs/project.html', {'project': item, 'documents': documents, 'query': query})

def document(request, project_slug, slug, version_id=None):
    item = get_object_or_404(Document.objects.select_related('project'), project__slug=project_slug, slug=slug)
    versions = item.versions.filter(status=Version.Status.PUBLISHED).select_related('author')
    if version_id is not None:
        selected = get_object_or_404(versions, pk=version_id)
    else:
        selected = versions.first()
        if selected is None:
            from django.http import Http404
            raise Http404('Нет опубликованных версий')
    return render(request, 'docs/document.html', {'document': item, 'version': selected, 'versions': versions})
