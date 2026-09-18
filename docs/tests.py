from django.test import TestCase, Client
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db.models import ProtectedError
from .models import Project, Document, Author, Version


class PublicationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)

    def test_catalog_and_search(self):
        response = self.client.get('/')
        self.assertContains(response, 'Платформа ТехДок')
        response = self.client.get('/projects/techdocs/', {'q': 'Регламент'})
        self.assertContains(response, 'Регламент публикации')
        self.assertNotContains(response, 'Быстрый старт')

    def test_latest_and_historical_version(self):
        document = Document.objects.get(slug='quickstart')
        response = self.client.get(document.get_absolute_url())
        self.assertEqual(response.context['version'].number, '1.1')
        old = document.versions.get(number='1.0')
        response = self.client.get(f'{document.get_absolute_url()}versions/{old.pk}/')
        self.assertEqual(response.context['version'].number, '1.0')

    def test_draft_is_private_even_with_direct_url(self):
        draft = Version.objects.get(status='draft')
        response = self.client.get(f'{draft.document.get_absolute_url()}versions/{draft.pk}/')
        self.assertEqual(response.status_code, 404)
        response = self.client.get(draft.document.get_absolute_url())
        self.assertNotContains(response, draft.content)

    def test_document_with_only_draft_is_hidden(self):
        document = Document.objects.create(project=Project.objects.first(), title='Секретный черновик', slug='draft-only', summary='Недоступный текст')
        Version.objects.create(document=document, author=Author.objects.first(), number='0.1', content='Скрыто', change_note='Начало')
        self.assertEqual(self.client.get(document.get_absolute_url()).status_code, 404)
        self.assertNotContains(self.client.get(document.project.get_absolute_url()), 'Секретный черновик')

    def test_publication_sets_timestamp_and_makes_visible(self):
        draft = Version.objects.get(status='draft')
        self.assertIsNone(draft.published_at)
        draft.status = 'published'
        draft.save()
        self.assertIsNotNone(draft.published_at)
        response = self.client.get(draft.document.get_absolute_url())
        self.assertContains(response, draft.content)

    def test_published_version_is_immutable(self):
        version = Version.objects.filter(status='published').first()
        version.content = 'Изменённый текст'
        with self.assertRaises(ValidationError):
            version.save()

    def test_duplicate_number_rejected(self):
        version = Version.objects.first()
        with self.assertRaises(ValidationError):
            Version.objects.create(document=version.document, author=version.author, number=version.number,
                content='Дубликат', change_note='Повтор')

    def test_referenced_author_cannot_be_deleted(self):
        with self.assertRaises(ProtectedError):
            Version.objects.first().author.delete()

    def test_html_is_escaped(self):
        draft = Version.objects.get(status='draft')
        draft.content = '<script>alert(1)</script>'
        draft.status = 'published'
        draft.save()
        response = self.client.get(draft.document.get_absolute_url())
        self.assertNotContains(response, '<script>')
        self.assertContains(response, '&lt;script&gt;')

    def test_admin_requires_login(self):
        self.assertEqual(self.client.get('/admin/docs/version/').status_code, 302)

    def test_unknown_document_returns_404(self):
        self.assertEqual(self.client.get('/projects/techdocs/missing/').status_code, 404)

    def test_seed_is_idempotent(self):
        before = [m.objects.count() for m in [Project, Document, Author, Version]]
        call_command('seed_demo', verbosity=0)
        self.assertEqual(before, [m.objects.count() for m in [Project, Document, Author, Version]])

    def test_admin_publication_form(self):
        user = get_user_model().objects.create_superuser('tester', 'test@example.com', 'test-only-password')
        self.client.force_login(user)
        draft = Version.objects.get(status='draft')
        response = self.client.post(f'/admin/docs/version/{draft.pk}/change/', {
            'document': draft.document_id, 'author': draft.author_id, 'number': draft.number,
            'content': draft.content, 'change_note': draft.change_note, 'status': 'published', '_save': 'Сохранить'})
        self.assertEqual(response.status_code, 302)
        draft.refresh_from_db()
        self.assertEqual(draft.status, 'published')

    def test_csrf_is_required_for_admin_post(self):
        response = Client(enforce_csrf_checks=True).post('/admin/login/', {'username': 'someone', 'password': 'x'})
        self.assertEqual(response.status_code, 403)
