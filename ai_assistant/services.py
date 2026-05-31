import openai
import json
from django.conf import settings
from django.utils import timezone
from service.models import Habit, Task
from .models import AIChatMessage

class AIAgentService:
    def __init__(self, user):
        self.user = user
        self.client = openai.OpenAI(api_key=getattr(settings, "OPENAI_API_KEY", "no-key"))

    def get_user_context(self):
            today = timezone.now().date()
            all_habits = Habit.objects.filter(user=self.user)
            
            habits_schedule = []
            for h in all_habits:
                days = ", ".join(h.frequency) if isinstance(h.frequency, list) else h.frequency
                habits_schedule.append(f"- {h.name}: every {days}")

            next_week = today + timezone.timedelta(days=7)
            upcoming_tasks = Task.objects.filter(
                user=self.user, 
                date__range=[today, next_week]
            ).order_by('date')
            
            tasks_info = [f"{t.title} on {t.date.strftime('%A, %B %d')}" for t in upcoming_tasks]

            return {
                "today_date": today.strftime("%A, %B %d, %Y"),
                "habits_schedule": "\n".join(habits_schedule) or "no recurring habits",
                "upcoming_tasks": "; ".join(tasks_info) or "no tasks for the next 7 days",
                "stats_today": f"{all_habits.filter(status='done').count()}/{all_habits.count()} total habits tracked"
            }
            
    def detect_burnout_signals(self):
        from service.models import Progress
        today = timezone.now().date()
        week_ago = today - timezone.timedelta(days=7)
        
        recent = Progress.objects.filter(user=self.user, date__gte=week_ago)
        total = recent.count()
        missed = recent.filter(status='missed').count()
        
        if total > 0 and missed / total > 0.5:
            return "burnout_risk"
        if self.user.current_overall_streak == 0 and self.user.best_overall_streak > 5:
            return "streak_broken"
        return None

    def create_new_task(self, title, date):
        try:
            Task.objects.create(user=self.user, title=title, date=date)
            return f"Success: Task '{title}' has been scheduled for {date}."
        except Exception as e:
            return f"Error: Could not create task. {str(e)}"

    def delete_task_by_title(self, title):
        try:
            tasks = Task.objects.filter(user=self.user, title__icontains=title)
            if tasks.exists():
                count = tasks.count()
                tasks.delete()
                return f"Success: Deleted {count} task(s) with title '{title}'."
            return f"Notice: No tasks found with title '{title}' to delete."
        except Exception as e:
            return f"Error: Could not delete task. {str(e)}"

    def get_response(self, user_message):
        context = self.get_user_context()
        AIChatMessage.objects.create(user=self.user, role='user', content=user_message)

        history_objs = AIChatMessage.objects.filter(user=self.user).order_by('-timestamp')[:10]
        chat_history = [{"role": msg.role, "content": msg.content} for msg in reversed(history_objs)]

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "create_new_task",
                    "description": "Schedules a new task. Use ONLY when the user explicitly asks to add or schedule something.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Task title"},
                            "date": {"type": "string", "description": "YYYY-MM-DD"}
                        },
                        "required": ["title", "date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_task_by_title",
                    "description": "Deletes a task. Use ONLY when the user explicitly asks to remove or delete something.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Title of the task to delete"}
                        },
                        "required": ["title"]
                    }
                }
            }
        ]

        burnout = self.detect_burnout_signals()

        if burnout == "burnout_risk":
            tone = (
                "The user is showing signs of burnout — over 50% of habits missed this week. "
                "Do NOT mention what they failed to do. Be warm and gentle. "
                "Suggest reducing habits to 2-3 for this week. No pressure, no judgement."
            )
        elif burnout == "streak_broken":
            tone = (
                "The user just broke a good streak. Do NOT focus on the failure. "
                "Acknowledge it briefly, then suggest one easy 'reset day' to start fresh. "
                f"Remind them their best streak was {self.user.best_overall_streak} days — "
                "that's proof they can do it again."
            )
        else:
            tone = "Be encouraging, specific, and motivating. Reference habit names directly."

        system_instructions = (
            f"You are the Lumos Flow AI Mentor. Today is {context['today_date']}. "
            f"User's habit schedule:\n{context['habits_schedule']}\n"
            f"Upcoming tasks: {context['upcoming_tasks']}.\n"
            f"Today's progress: {context['stats_today']}.\n"
            f"When the user asks about ANY day (like Sunday, next week, etc.), "
            "check the 'General Habit Schedule' to see which habits fall on those days. "
            "For tasks, only report what is in the 'Upcoming Tasks' list. "
            f"Tone guidance: {tone}"
        )
        messages = [{"role": "system", "content": system_instructions}]
        messages.extend(chat_history)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.7
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                messages.append(response_message)
                for tool_call in tool_calls:
                    func_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    
                    if func_name == "create_new_task":
                        result = self.create_new_task(args.get("title"), args.get("date"))
                    elif func_name == "delete_task_by_title":
                        result = self.delete_task_by_title(args.get("title"))
                    
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": func_name,
                        "content": result,
                    })

                second_response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                )
                ai_reply = second_response.choices[0].message.content
            else:
                ai_reply = response_message.content

            AIChatMessage.objects.create(user=self.user, role='assistant', content=ai_reply)
            return ai_reply

        except Exception as e:
            print(f"OpenAI Error: {e}")
            return self.get_fallback_logic(user_message, context)

    def get_fallback_logic(self, msg, context):
        msg = msg.lower()
        if any(word in msg for word in ["tired", "exhausted", "burnout", "broke", "failed"]):
            return f"I hear you. You've done {context['stats_today']} today. Rest is part of progress. 🌿"
        if any(word in msg for word in ["task", "todo", "schedule", "today", "week"]):
            return f"Your upcoming tasks: {context['upcoming_tasks']}. You can do this! ✨"
        return "I'm in offline mode right now, but I'm still here supporting your progress! 💪"