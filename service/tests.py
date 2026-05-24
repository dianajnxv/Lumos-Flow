from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Habit, Category, Task
from datetime import date, timedelta

User = get_user_model()

class LumosFlowCoreTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='developer_test', 
            email='dev@lumosflow.com', 
            password='securepassword123'
        )
        self.category = Category.objects.create(
            name="Health & Wellness", 
            description="Habits related to physical and mental health"
        )

    def test_user_initial_state(self):
        self.assertEqual(self.user.theme, "light")
        self.assertEqual(self.user.current_overall_streak, 0)
        self.assertEqual(self.user.best_overall_streak, 0)

    def test_habit_structure_and_category(self):
        habit = Habit.objects.create(
            user=self.user,
            name="Early Morning Run",
            category=self.category,
            priority='high',
            frequency=["mon", "wed", "fri"]
        )
        self.assertEqual(habit.status, 'not_done')
        self.assertEqual(habit.get_priority_display(), 'High')
        self.assertIn("mon", habit.frequency)

    def test_task_creation_for_ai_logic(self):
        future_date = date.today() + timedelta(days=1)
        task = Task.objects.create(
            user=self.user,
            title="Read 20 pages of a book",
            date=future_date,
            priority='medium'
        )
        self.assertFalse(task.is_completed)
        self.assertEqual(task.date, future_date)

    def test_streak_automation_via_signals(self):
        Habit.objects.create(
            user=self.user,
            name="Drink Water",
            category=self.category,
            status='done'
        )
        
        self.user.refresh_from_db()
        
        self.assertEqual(self.user.current_overall_streak, 1)
        self.assertEqual(self.user.best_overall_streak, 1)