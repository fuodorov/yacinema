import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from model_utils.models import TimeStampedModel
from django.conf import settings


CONTENT_SCHEMA = getattr(settings, 'CONTENT_SCHEMA', 'content')


class Person(TimeStampedModel):
    id = models.UUIDField(_('id'), primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.TextField(_('Full name'))
    birth_date = models.DateField(_('Birthday'), null=True)

    class Meta:
        verbose_name = _('Person')
        verbose_name_plural = _('Persons')
        managed = False
        db_table = f'{CONTENT_SCHEMA}"."person'

    def __str__(self):
        return self.full_name


class Genre(TimeStampedModel):
    id = models.UUIDField(_('id'), primary_key=True, default=uuid.uuid4, editable=False)
    name = models.TextField(_('Name'))
    description = models.TextField(_('Description'), blank=True)

    class Meta:
        verbose_name = _('Genre')
        verbose_name_plural = _('Genres')
        managed = False
        db_table = f'{CONTENT_SCHEMA}"."genre'

    def __str__(self):
        return self.name


class FilmWorkType(models.TextChoices):
    MOVIE = ('film', _('Film'))
    SERIES = ('series', _('Series'))


class FilmWork(TimeStampedModel):
    id = models.UUIDField(_('id'), primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('Name'), max_length=255)
    description = models.TextField(_('Description'), blank=True)
    creation_date = models.DateField(_('Creation date'), null=True, blank=True)
    certificate = models.TextField(_('Certificate'), blank=True)
    file_path = models.FileField(_('File'), upload_to='film_works/', null=True, blank=True)
    rating = models.FloatField(_('Rating'), validators=[MinValueValidator(0), MaxValueValidator(10)],
                               null=True, blank=True)
    type = models.TextField(_('Type'), choices=FilmWorkType.choices, blank=True)
    genres = models.ManyToManyField('movies.Genre', through='movies.GenreFilmWork')
    persons = models.ManyToManyField('movies.Person', through='movies.PersonFilmWork')

    class Meta:
        verbose_name = _('Film')
        verbose_name_plural = _('Films')
        managed = False
        db_table = f'{CONTENT_SCHEMA}"."film_work'

    def __str__(self):
        return self.title

    def list_genres(self):
        return ', '.join([str(genre) for genre in self.genres.all()])


class RoleType(models.TextChoices):
    ACTOR = ('actor', _('Actor'))
    WRITER = ('writer', _('Writer'))
    DIRECTOR = ('director', _('Director'))


class PersonFilmWork(models.Model):
    id = models.UUIDField(_('id'), primary_key=True, default=uuid.uuid4, editable=False)
    film_work = models.ForeignKey('movies.FilmWork', on_delete=models.CASCADE)
    person = models.ForeignKey('movies.Person', on_delete=models.CASCADE)
    role = models.TextField(_('Role'), choices=RoleType.choices)
    created = models.DateTimeField(_('Created'), auto_created=True, auto_now_add=True)

    class Meta:
        verbose_name = _('Person')
        verbose_name_plural = _('Persons')
        db_table = f'{CONTENT_SCHEMA}"."person_film_work'
        managed = False
        unique_together = ('film_work', 'person', 'role')


class GenreFilmWork(models.Model):
    id = models.UUIDField(_('id'), primary_key=True, default=uuid.uuid4, editable=False)
    film_work = models.ForeignKey('movies.FilmWork', on_delete=models.CASCADE)
    genre = models.ForeignKey('movies.Genre', on_delete=models.CASCADE)
    created = models.DateTimeField(_('Created'), auto_created=True, auto_now_add=True)

    class Meta:
        verbose_name = _('Genre')
        verbose_name_plural = _('Genres')
        db_table = f'{CONTENT_SCHEMA}"."genre_film_work'
        managed = False
        unique_together = ('film_work', 'genre')
