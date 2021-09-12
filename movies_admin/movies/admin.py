from django.contrib import admin
from .models import FilmWork, Person, Genre


class PersonInLineAdmin(admin.TabularInline):
    model = FilmWork.persons.through
    extra = 0


class GenreInLineAdmin(admin.TabularInline):
    model = FilmWork.genres.through
    extra = 0


@admin.register(FilmWork)
class FilmWorkAdmin(admin.ModelAdmin):
    list_display = ('title', 'type', 'creation_date', 'rating')
    list_filter = ('type',)
    fields = ('title', 'type', 'description', 'creation_date', 'rating', 'certificate', 'file_path')
    inlines = (PersonInLineAdmin, GenreInLineAdmin)
    search_fields = ('title', 'description', 'type', 'genres')


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'birth_date')
    fields = ('full_name', 'birth_date')
    inlines = (PersonInLineAdmin,)
    search_fields = ('full_name', 'birth_date')


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    fields = ('name', 'description')
    inlines = (GenreInLineAdmin, )
    search_fields = ('name', 'description')
