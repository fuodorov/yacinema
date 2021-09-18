from rest_framework.fields import ReadOnlyField
from rest_framework.relations import SlugRelatedField
from rest_framework.serializers import ModelSerializer

from movies.models import Person, Genre, FilmWork


class PersonSerializer(ModelSerializer):

    class Meta:
        model = Person
        exclude = ('created', 'modified')


class GenreSerializer(ModelSerializer):

    class Meta:
        model = Genre
        exclude = ('created', 'modified')


class FilmWorkSerializer(ModelSerializer):
    actors, writers, directors = ReadOnlyField(), ReadOnlyField(), ReadOnlyField()
    genres = SlugRelatedField(many=True, read_only=True, slug_field='name')

    class Meta:
        model = FilmWork
        exclude = ('persons', 'created', 'modified', 'file_path', 'certificate')
