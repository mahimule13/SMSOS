from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import admin_required, role_required
from .models import Book, BookIssue
from apps.students.models import Student
from datetime import date, timedelta


@login_required(login_url='login')
def book_list(request):
    books = Book.objects.filter(is_active=True)
    context = {'books': books}
    return render(request, 'library/list.html', context)


@login_required(login_url='login')
@role_required('librarian')
def issue_book(request):
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        student_id = request.POST.get('student_id')
        due_days = request.POST.get('due_days', 14)
        
        book = Book.objects.get(id=book_id)
        student = Student.objects.get(id=student_id)
        
        if book.available_quantity > 0:
            due_date = date.today() + timedelta(days=int(due_days))
            
            BookIssue.objects.create(
                book=book,
                student=student,
                due_date=due_date,
                issued_by=request.user
            )
            
            book.available_quantity -= 1
            book.save()
            
            messages.success(request, 'Book issued successfully')
        else:
            messages.error(request, 'Book not available')
    
    books = Book.objects.filter(is_active=True)
    students = Student.objects.filter(is_active=True)
    context = {'books': books, 'students': students}
    return render(request, 'library/issue.html', context)


@login_required(login_url='login')
@role_required('librarian')
def return_book(request):
    if request.method == 'POST':
        issue_id = request.POST.get('issue_id')
        issue = BookIssue.objects.get(id=issue_id)
        
        issue.returned_date = date.today()
        issue.status = 'returned'
        issue.returned_by = request.user
        issue.save()
        
        # Increase available quantity
        issue.book.available_quantity += 1
        issue.book.save()
        
        messages.success(request, 'Book returned successfully')
    
    issued_books = BookIssue.objects.filter(status='issued')
    context = {'issued_books': issued_books}
    return render(request, 'library/return.html', context)


@login_required(login_url='login')
@role_required('librarian')
def library_reports(request):
    total_books = Book.objects.count()
    available = Book.objects.aggregate(models.Sum('available_quantity'))['available_quantity__sum'] or 0
    issued = BookIssue.objects.filter(status='issued').count()
    overdue = BookIssue.objects.filter(status='issued', due_date__lt=date.today()).count()
    
    context = {
        'total_books': total_books,
        'available': available,
        'issued': issued,
        'overdue': overdue,
    }
    return render(request, 'library/reports.html', context)
