from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Habit, Progress
from .service import AchievementService
from datetime import date, timedelta

@receiver(post_save, sender=Habit)
def habit_saved_handler(sender, instance, created, **kwargs):
    if instance.status == 'done':
        _update_streaks_in_db(instance.user)
        AchievementService.check_and_grant_achievements(instance.user)

def _update_streaks_in_db(user):
    today = date.today()
    completed_dates = (
        Progress.objects
        .filter(user=user, status='completed')
        .values_list('date', flat=True)
        .order_by('-date')
        .distinct()
    )

    dates_list = list(completed_dates)
    new_current_streak = 0

    if dates_list:
        if dates_list[0] == today or dates_list[0] == (today - timedelta(days=1)):
            new_current_streak = 1
            for i in range(len(dates_list) - 1):
                if (dates_list[i] - dates_list[i+1]).days == 1:
                    new_current_streak += 1
                else:
                    break

    if user.current_overall_streak != new_current_streak:
        user.current_overall_streak = new_current_streak
        if new_current_streak > user.best_overall_streak:
            user.best_overall_streak = new_current_streak
        user.save(update_fields=['current_overall_streak', 'best_overall_streak'])