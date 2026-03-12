@login_required
@i_rzbac(operation='record:view')
def view_patient_record(request, patient_id):
    # view record
    return JsonResponse({'record': 'sample record'})

@login_required
@n_rzbac(operation='prescribe')
def prescribe(request):
    # create prescription (SoD constraint will be checked if context includes patient_id)
    data = json.loads(request.body)
    # Here you would need to pass context; for now just return
    return JsonResponse({'status': 'prescribed'})