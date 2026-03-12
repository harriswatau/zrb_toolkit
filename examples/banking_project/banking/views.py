import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from zrb.web.django import i_rzbac, n_rzbac
from .models import Account, Transaction

@login_required
@i_rzbac(operation='balance:view')
def view_balance(request, account_id):
    try:
        account = Account.objects.get(id=account_id)
        return JsonResponse({'account': account.account_number, 'balance': str(account.balance)})
    except Account.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

@login_required
@csrf_exempt
@i_rzbac(operation='withdraw')
def withdraw(request):
    data = json.loads(request.body)
    amount = data.get('amount', 0)
    account_id = data.get('account_id')
    # Additional business logic (check balance, etc.)
    return JsonResponse({'status': 'withdrawal processed'})

@login_required
@csrf_exempt
@n_rzbac(operation='transaction:approve_high')
def approve_high_transaction(request):
    data = json.loads(request.body)
    transaction_id = data.get('transaction_id')
    # Approve transaction
    return JsonResponse({'status': 'approved'})

# Additional endpoints: deposit, loan processing, audit, etc.