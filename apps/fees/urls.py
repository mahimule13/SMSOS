from django.urls import path
from . import views_fixed as views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'fees'

urlpatterns = [
    path('', views.fee_list, name='list'),
    path('collection/', views.fee_collection, name='collection'),
    path('structure/', views.fee_structure, name='structure'),
    path('reports/', views.fee_reports, name='reports'),

    # Student payment
    path('student/pay/', views.student_pay, name='student_pay'),

    # Receipt URLs ✅
    path('receipt/download/<path:filename>/', views.download_receipt, name='download_receipt'),
    path('receipt/preview/<path:filename>/', views.receipt_preview, name='receipt_preview')
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )


