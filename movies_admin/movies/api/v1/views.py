from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ReadOnlyModelViewSet

from movies.api.v1.serializers import PersonSerializer, GenreSerializer, FilmWorkSerializer
from movies.api.v1.filters import PersonFilter, GenreFilter, FilmWorkFilter
from movies.models import Person, Genre, FilmWork


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
    queryset = FilmWork.objects.all()
