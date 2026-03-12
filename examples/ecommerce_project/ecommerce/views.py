@login_required
@i_rzbac(operation='order:create')
def create_order(request):
    # create order
    return JsonResponse({'status': 'order created'})

@login_required
@n_rzbac(operation='discount:approve')
def approve_discount(request):
    # approve discount
    return JsonResponse({'status': 'discount approved'})