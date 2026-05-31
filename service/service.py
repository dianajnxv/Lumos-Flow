from django.db.models import Q
from .models import Habit, Achievement

class AchievementService:
    @staticmethod
    def check_and_grant_achievements(user):
        owned_keys = user.achievements.values_list('key', flat=True)
        all_done_habits = Habit.objects.filter(user=user, status='done')
        all_done_count = all_done_habits.count()

        if 'first_step' not in owned_keys:
            if all_done_count >= 1:
                AchievementService._grant(user, 'first_step')

        if 'total_100' not in owned_keys:
            if all_done_count >= 100:
                AchievementService._grant(user, 'total_100')

        if 'diploma_10' not in owned_keys:
            diploma_count = all_done_habits.filter(
                Q(name__icontains="Diploma") | Q(name__icontains="Диплом")
            ).count()
            if diploma_count >= 10:
                AchievementService._grant(user, 'diploma_10')

        if 'zen_20' not in owned_keys:
            zen_count = all_done_habits.filter(
                Q(name__icontains="Meditate") | Q(name__icontains="Медитація")
            ).count()
            if zen_count >= 20:
                AchievementService._grant(user, 'zen_20')

        if 'streak_7' not in owned_keys:
            if user.current_overall_streak >= 7:
                AchievementService._grant(user, 'streak_7')

        if 'streak_14' not in owned_keys:
            if user.current_overall_streak >= 14:
                AchievementService._grant(user, 'streak_14')

        if 'streak_30' not in owned_keys:
            if user.current_overall_streak >= 30:
                AchievementService._grant(user, 'streak_30')

    @staticmethod
    def _grant(user, achievement_key):
        try:
            achievement = Achievement.objects.get(key=achievement_key)
            user.achievements.add(achievement)
        except Achievement.DoesNotExist:
            pass