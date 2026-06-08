from django.contrib import admin
from .models import FeeStructure, FeeCollection, FeeReceipt, FinePenalty


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):

    list_display = (
        'class_name',
        'fee_type',
        'amount',
        'is_active',
        'created_at',
    )

    list_filter = (
        'fee_type',
        'is_active',
    )

    search_fields = (
        'class_name',
        'fee_type',
    )


@admin.register(FeeCollection)
class FeeCollectionAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'fee_structure',
        'month',
        'amount_due',
        'amount_paid',
        'status',
    )

    list_filter = (
        'status',
        'payment_method',
    )

    search_fields = (
        'student__name',
    )


@admin.register(FeeReceipt)
class FeeReceiptAdmin(admin.ModelAdmin):

    list_display = (
        'receipt_number',
        'fee_collection',
        'issued_date',
        'issued_by',
    )


@admin.register(FinePenalty)
class FinePenaltyAdmin(admin.ModelAdmin):

    list_display = (
        'fee_collection',
        'fine_amount',
        'created_at',
    )