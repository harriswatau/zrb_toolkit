@login_required
@i_rzbac(operation='task:assign')
def assign_task(request):
    # assign task
    return JsonResponse({'status': 'task assigned'})

@login_required
@i_rzbac(operation='review:approve')
def approve_review(request):
    # approve pull request (context should include author_id)
    data = json.loads(request.body)
    # In a real app, you'd pass context to the engine via a custom decorator or direct call
    # For simplicity, we rely on the decorator's default behavior (no context)
    # To enforce SoD, you would need to extend the decorator or call engine.decide directly.
    return JsonResponse({'status': 'review approved'})