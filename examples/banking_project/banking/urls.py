from django.urls import path
from . import views

urlpatterns = [
    path('balance/<int:account_id>/', views.view_balance, name='view_balance'),
    path('withdraw/', views.withdraw, name='withdraw'),
    path('approve-high/', views.approve_high_transaction, name='approve_high'),
    # ...
]