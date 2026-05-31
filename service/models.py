from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class ThemeChoices(models.TextChoices):
    LIGHT = "light", "Light Theme"
    DARK = "dark", "Dark Theme"
    MOTIVATING = "motivating", "Motivating Theme"

class CustomUser(AbstractUser):
    bio = models.TextField(
        blank=True,
        max_length=250
    )
    email = models.EmailField(
        unique=True,
        db_index=True
    )
    theme = models.CharField(
        max_length=20,
        choices=ThemeChoices.choices,
        default=ThemeChoices.LIGHT
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        default='avatars/avatar.jpg'
    )

    current_overall_streak = models.PositiveIntegerField(
        default=0
    )
    best_overall_streak = models.PositiveIntegerField(
        default=0
    )

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True
    )

    class Meta:
        verbose_name = "Custom User"
        verbose_name_plural = "Custom Users"

    def __str__(self):
        return self.username

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

class Habit(models.Model):
    DAYS_OF_WEEK = [
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
        ('sun', 'Sunday'),
    ]

    STATUS_CHOICES = [
        ('not_done', 'Not Done'),
        ('done', 'Done'),
        ('missed', 'Missed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='habits')
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
        related_name='habits'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    frequency = models.JSONField(
        default=list
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='not_done'
    )

    last_completed = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_frequency_display(self):
        day_names = dict(self.DAYS_OF_WEEK)
        return ", ".join([day_names.get(day, day) for day in self.frequency])

class Schedule(models.Model):
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('not_completed', 'Not Completed'),
        ('skipped', 'Skipped')
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='schedules')
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='schedules')
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_completed'
    )

    def __str__(self):
        return f"{self.habit.name} on {self.date} at {self.time}"

class Reminder(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ]

    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, related_name='reminders')
    email = models.EmailField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active'
    )

    def __str__(self):
        return f"Reminder for {self.schedule.habit.name} ({self.status})"

class Progress(models.Model):
    STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('not_completed', 'Not Completed'),
        ('skipped', 'Skipped')
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='progresses')
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='progresses')
    date = models.DateField()
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='not_completed'
    )

    def __str__(self):
        return f"{self.habit.name} on {self.date} - {self.status}"

class Achievement(models.Model):
    user_model = settings.AUTH_USER_MODEL

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image_name = models.CharField(max_length=255)
    key = models.CharField(max_length=50, unique=True)
    users = models.ManyToManyField(user_model, related_name='achievements', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Statistic(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='statistics')
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='statistics')
    period = models.DurationField()
    completed = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Stats for {self.habit.name} ({self.period})"

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)
    time = models.TimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    class Meta:
        ordering = ['date', 'time']

    def __str__(self):
        return f"{self.title} on {self.date}"