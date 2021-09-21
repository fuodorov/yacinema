from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ReadOnlyModelViewSet

from movies.api.v1.serializers import PersonSerializer, GenreSerializer, FilmWorkSerializer
from movies.api.v1.filters import PersonFilter, GenreFilter, FilmWorkFilter
from movies.models import Person, Genre, FilmWork, RoleType


class PersonViewSet(ReadOnlyModelViewSet):
    serializer_class = PersonSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = PersonFilter
    queryset = Person.objects.all()


class GenreViewSet(ReadOnlyModelViewSet):
    serializer_class = GenreSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = GenreFilter
    queryset = Genre.objects.all()


class FilmWorkViewSet(ReadOnlyModelViewSet):
    serializer_class = FilmWorkSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = FilmWorkFilter
    queryset = FilmWork.objects.annotate(
        writers=ArrayAgg('personfilmwork__person__full_name',
                         filter=Q(personfilmwork__role=RoleType.WRITER), distinct=True),
        actors=ArrayAgg('personfilmwork__person__full_name',
                        filter=Q(personfilmwork__role=RoleType.ACTOR), distinct=True),
        directors=ArrayAgg('personfilmwork__person__full_name',
                           filter=Q(personfilmwork__role=RoleType.DIRECTOR), distinct=True),
    )
