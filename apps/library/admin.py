from django.contrib import admin
from .models import Book, BookIssue


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'quantity', 'available_quantity', 'is_active')
    list_filter = ('is_active', 'category')
    search_fields = ('title', 'author', 'isbn')


@admin.register(BookIssue)
class BookIssueAdmin(admin.ModelAdmin):
    list_display = ('book', 'student', 'issued_date', 'due_date', 'status')
    list_filter = ('status', 'issued_date')
