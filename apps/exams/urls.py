from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    path('', views.exam_list, name='list'),
    path('create/', views.create_exam, name='create'),
    path('<int:pk>/', views.exam_detail, name='detail'),
    path('<int:pk>/marks/', views.mark_entry, name='mark_entry'),

    # Teacher: create exam timetable by section
    path('teacher/exam-schedule/create/', views.teacher_exam_schedule_create, name='teacher_exam_schedule_create'),

    # Teacher direct marks entry (active exam)
    path('teacher/marks/', views.teacher_mark_entry, name='teacher_mark_entry'),

    path('reportcard/<int:student_id>/', views.student_reportcard, name='reportcard'),
]



