from rest_framework.fields import ReadOnlyField
from rest_framework.relations import HyperlinkedRelatedField
from rest_framework.serializers import ModelSerializer

from movies.models import Person, Genre, FilmWork


class PersonSerializer(ModelSerializer):

    class Meta:
        model = Person
        fields = '__all__'


class GenreSerializer(ModelSerializer):

    class Meta:
        model = Genre
        fields = '__all__'


class FilmWorkSerializer(ModelSerializer):
    actors, writers, directors = ReadOnlyField(), ReadOnlyField(), ReadOnlyField()

    class Meta:
        model = FilmWork
        exclude = ('persons',)
