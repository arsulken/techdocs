from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError

class Author(models.Model):
    full_name = models.CharField('ФИО', max_length=200)
    email = models.EmailField('Электронная почта', unique=True)
    class Meta:
        verbose_name = 'автор'
        verbose_name_plural = 'авторы'
        ordering = ['full_name']
    def __str__(self):
        return self.full_name

class Project(models.Model):
    title = models.CharField('Название', max_length=200)
    slug = models.SlugField('Адрес', unique=True)
    description = models.TextField('Описание')
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    class Meta:
        verbose_name = 'проект'
        verbose_name_plural = 'проекты'
        ordering = ['title']
    def __str__(self):
        return self.title
    def get_absolute_url(self):
        return reverse('docs:project', args=[self.slug])

class Document(models.Model):
    project = models.ForeignKey(Project, on_delete=models.PROTECT,
        related_name='documents', verbose_name='Проект')
    title = models.CharField('Название', max_length=200)
    slug = models.SlugField('Адрес')
    summary = models.TextField('Краткое описание')
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    class Meta:
        verbose_name = 'документ'
        verbose_name_plural = 'документы'
        ordering = ['title']
        constraints = [models.UniqueConstraint(fields=['project', 'slug'], name='unique_document_slug')]
    def __str__(self):
        return self.title
    def get_absolute_url(self):
        return reverse('docs:document', args=[self.project.slug, self.slug])

class Version(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Черновик'
        PUBLISHED = 'published', 'Опубликована'
    document = models.ForeignKey(Document, on_delete=models.PROTECT,
        related_name='versions', verbose_name='Документ')
    author = models.ForeignKey(Author, on_delete=models.PROTECT,
        related_name='versions', verbose_name='Автор')
    number = models.CharField('Номер версии', max_length=32, help_text='Например: 1.0 или 2.1')
    content = models.TextField('Содержимое', help_text='Обычный текст; HTML не исполняется.')
    change_note = models.CharField('Описание изменений', max_length=255)
    status = models.CharField('Статус', max_length=12, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    published_at = models.DateTimeField('Опубликована', null=True, blank=True, editable=False)
    class Meta:
        verbose_name = 'версия'
        verbose_name_plural = 'версии'
        ordering = ['-published_at', '-pk']
        constraints = [models.UniqueConstraint(fields=['document', 'number'], name='unique_version_number'),
            models.CheckConstraint(condition=(models.Q(status='draft', published_at__isnull=True) |
                models.Q(status='published', published_at__isnull=False)), name='consistent_publication')]
    def __str__(self):
        return f'{self.document} / {self.number}'
    def clean(self):
        super().clean()
        if self.pk:
            previous = type(self).objects.get(pk=self.pk)
            if previous.status == self.Status.PUBLISHED:
                fields = ['document_id', 'author_id', 'number', 'content', 'change_note', 'status']
                if any(getattr(previous, f) != getattr(self, f) for f in fields):
                    raise ValidationError('Опубликованную версию нельзя изменять. Создайте новую версию.')
        self.published_at = (self.published_at or timezone.now()) if self.status == self.Status.PUBLISHED else None
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
