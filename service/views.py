import json
import os
from datetime import date, datetime, timedelta
from functools import wraps

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models.functions import ExtractWeekDay

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm

from .forms import (
    CustomUserCreationForm,
    CustomAuthenticationForm,
    SubscribeForm,
    HabitForm
)

from .models import CustomUser, Progress, Habit, Category, Task

ALLOWED_EXTENSIONS = ['.png', '.jpg', '.jpeg']

MAX_IMAGE_SIZE = 10 * 1024 * 1024 

DAYS = [
    ("Monday", "M"),
    ("Tuesday", "T"),
    ("Wednesday", "W"),
    ("Thursday", "T"),
    ("Friday", "F"),
    ("Saturday", "S"),
    ("Sunday", "S"),
]

def validate_avatar(file):
    extension = os.path.splitext(file.name)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError(f'Unsupported file format. Allowed formats: {", ".join(ALLOWED_EXTENSIONS)}')

    if file.size > MAX_IMAGE_SIZE:
        raise ValidationError(f'File size exceeds the maximum allowed size of {MAX_IMAGE_SIZE / 1024 / 1024} MB.')

def user_is_owner(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        username = kwargs.get('username')
        if request.user.username != username:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

def home_view(request):
    context = {
        'category_list': Category.objects.all(),
        'theme': 'light',
        'days': DAYS,
    }

    if request.user.is_authenticated:
        context['theme'] = request.user.theme

    return render(request, 'home.html', context)


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


@login_required(login_url='login')
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('home')
    return render(request, 'logout.html')

def profile_view(request, username):
    user = get_object_or_404(CustomUser, username=username)

    success_rate_data = Progress.objects.filter(user_id=user.id).aggregate(
        done=Count('id', filter=Q(status__iexact='completed')),  
        missed=Count('id', filter=Q(status__iexact='skipped')),
        not_done=Count('id', filter=Q(status__iexact='not_completed')) 
    )

    habits_data = Habit.objects.filter(user_id=user.id).values('category').annotate(count=Count('id'))

    activity_query = Progress.objects.filter(
        user_id=user.id, 
        status__iexact='completed', 
        date__gte=timezone.now() - timedelta(days=30)
    ).values('date').annotate(total=Count('id')).order_by('date')
    
    weekly = (
    Progress.objects.filter(user_id=user.id, status='completed')
    .annotate(day=ExtractWeekDay('date'))
    .values('day')
    .annotate(total=Count('id'))
    )

    week_map = [0] * 7
    for item in weekly:
        index = (item['day'] + 5) % 7
        week_map[index] = item['total']

    act_labels = [item['date'].strftime('%d %b') for item in activity_query]
    act_values = [item['total'] for item in activity_query]

    success_list = [
        success_rate_data['done'] or 0, 
        success_rate_data['missed'] or 0, 
        success_rate_data['not_done'] or 0
    ]
    
    done = success_rate_data['done'] or 0
    missed = success_rate_data['missed'] or 0
    not_done = success_rate_data['not_done'] or 0
    total = done + missed + not_done

    actual_success_rate = round((done / total * 100), 1) if total > 0 else 0

    context = {
        'profile_user': user,
        'habits_count': Habit.objects.filter(user_id=user.id).count(),
        'js_success_data': json.dumps(success_list),
        'js_cat_labels': json.dumps([item['category'] for item in habits_data]),
        'js_cat_counts': json.dumps([item['count'] for item in habits_data]),
        'js_act_labels': json.dumps(act_labels),
        'js_act_values': json.dumps(act_values),
        'js_weekly_activity': json.dumps(week_map),
        'success_percentage': actual_success_rate,
    }
    return render(request, 'profile.html', context)

@login_required(login_url='login')
@user_is_owner
def edit_profile_view(request, username):
    user = get_object_or_404(CustomUser, username=username)

    if request.method == 'POST':
        try:
            new_username = request.POST.get('new_username', user.username)
            new_bio = request.POST.get('bio', user.bio)

            if CustomUser.objects.filter(username=new_username).exists() and new_username != username:
                return JsonResponse({
                    'status': 'error',
                    'username_error': 'Username already exists, try another one.'
                })
            
            if len(new_bio) > 250:
                return JsonResponse({
                    'status': 'error',
                    'bio_error': f'This field is too long. Max 250 characters.'
                })

            user.username = new_username
            user.bio = new_bio

            if 'avatar' in request.FILES:
                avatar = request.FILES['avatar']
                try:
                    validate_avatar(avatar)
                    user.avatar = avatar
                except ValidationError as e:
                    return JsonResponse({'status': 'error', 'avatar_error': e.message})

            user.save()
            
            return JsonResponse({"status": "success"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

@csrf_exempt
def change_theme(request):
    if request.method == "POST":
        theme = request.POST.get("theme")
        if theme in ["light", "dark", "motivating"]:
            if request.user.is_authenticated:
                request.user.theme = theme
                request.user.save()
            request.session['theme'] = theme
            return JsonResponse({"status": "success", "message": "Theme updated successfully."})
        return JsonResponse({"status": "error", "message": "Invalid theme selected."}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request."}, status=400)

@csrf_exempt
def create_habit_view(request):
    if request.method == "POST" and request.user.is_authenticated:
        try:
            if not request.body:
                return JsonResponse({'success': False, 'error': 'Empty request body'})

            data = json.loads(request.body)
            name = data.get('name')
            category_id = data.get('category')
            days = data.get('days')
            priority = data.get('priority')

            new_habit = Habit.objects.create(
                name=name,
                category_id=category_id,
                frequency=days,  
                priority=priority,
                user_id=request.user.id,
            )

            return JsonResponse({'success': True})  

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON format'})

        except Exception as e:
            print(e)
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid method'})

def subscribe_view(request):
    if request.method == 'POST':
        form = SubscribeForm(request.POST)
        
        if form.is_valid():  
            email = form.cleaned_data['email']
            send_mail(
                'Thank you for subscribing!',
                'You will receive updates from us soon.',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            return redirect('subscribe-success')  
        else:  
            return render(request, 'home.html', {'form': form})
    else:
        form = SubscribeForm()
    
    return render(request, 'home.html', {'form': form})

@login_required
def schedule(request):
    habits = Habit.objects.filter(user=request.user)
    return render(request, 'schedule.html', {'habits': habits})

@login_required
def habit_delete(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    if request.method == 'POST':
        habit.delete()
    return redirect('schedule')

@login_required
def habit_edit(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    if request.method == 'POST':
        form = HabitForm(request.POST, instance=habit)
        if form.is_valid():
            form.save()
            return redirect('schedule')
    else:
        form = HabitForm(instance=habit)
    return render(request, 'habit_edit.html', {'form': form})

@login_required
def toggle_status(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    
    if request.method == 'POST':
        next_status_map = {'not_done': 'done', 'done': 'missed', 'missed': 'not_done'}
        new_status = next_status_map.get(habit.status, 'not_done')
        
        habit.status = new_status
        habit.save()

        habit_to_progress_status = {
            'done': 'completed',
            'missed': 'skipped',
            'not_done': 'not_completed',
        }
        progress_status = habit_to_progress_status.get(new_status, 'not_completed')

        Progress.objects.update_or_create(
            user=request.user,
            habit=habit,
            date=timezone.now().date(),
            defaults={'status': progress_status}
        )
        
    return redirect('schedule')

@login_required
def get_tasks(request):
    if request.method == 'GET':
        tasks = Task.objects.filter(user=request.user)
        data = []
        
        for task in tasks:
            data.append({
                'id': f'task-{task.id}',
                'title': task.title,
                'start': task.date.isoformat(),
                'className': 'calendar-task-event', 
                'extendedProps': {'type': 'task'}
            })

        habits = Habit.objects.filter(user=request.user)
        
        start_date = timezone.now().date() - timedelta(days=30)
        end_date = timezone.now().date() + timedelta(days=30)

        current_day = start_date
        while current_day <= end_date:
            day_name = current_day.strftime('%A').lower()
            
            for habit in habits:
                    if day_name in [d.lower() for d in habit.frequency]:
                        data.append({
                        'id': f'habit-{habit.id}-{current_day}',
                        'title': f' {habit.name}',
                        'start': current_day.isoformat(),
                        'className': 'calendar-habit-event', 
                        'allDay': True,
                        'extendedProps': {
                            'type': 'habit',
                            'habitId': habit.id
                        }
                    })
            current_day += timedelta(days=1)

        return JsonResponse(data, safe=False)
    return HttpResponseNotAllowed(['GET'])

@login_required
def add_task(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            title = data.get('title')
            date_str = data.get('date')
            if not title or not date_str:
                return JsonResponse({'status': 'error', 'message': 'Title and date are required'}, status=400)

            try:
                date_obj = datetime.fromisoformat(date_str).date()  
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid date format, expected YYYY-MM-DD'}, status=400)

            task = Task.objects.create(title=title, date=date_obj, user=request.user)
            return JsonResponse({
                'status': 'success',
                'id': task.id,
                'title': task.title,
                'date': task.date.isoformat()
            })
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    return HttpResponseNotAllowed(['POST'])

@login_required
def delete_task(request, task_id):
    if request.method == 'DELETE':
        try:
            task = Task.objects.get(id=task_id, user=request.user)
            task.delete()
            return JsonResponse({'status': 'success'})
        except Task.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Task not found'}, status=404)
    return HttpResponseNotAllowed(['DELETE'])

@login_required
def edit_task(request, task_id):
    if request.method == 'PUT':
        try:
            task = Task.objects.get(id=task_id, user=request.user)
        except Task.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Task not found'}, status=404)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

        new_title = data.get('title', '').strip()
        if not new_title:
            return JsonResponse({'status': 'error', 'message': 'Title cannot be empty'}, status=400)

        task.title = new_title
        task.save()
        return JsonResponse({'status': 'success'})
    return HttpResponseNotAllowed(['PUT'])

def get_ai_context(request):
    today = timezone.now().date()
    day_name = today.strftime('%A').lower()
    
    habits = Habit.objects.filter(user=request.user)
    today_habits = [h.name for h in habits if day_name in [d.lower() for d in h.frequency]]
    
    today_tasks = Task.objects.filter(user=request.user, date=today).values_list('title', flat=True)
    
    return JsonResponse({
    'habits_list': today_habits,
    'tasks_list': list(today_tasks)
})