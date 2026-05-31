function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

document.addEventListener("DOMContentLoaded", function () {
  const calendarEl = document.getElementById("task-calendar");
  const taskModal = document.getElementById("taskModal");
  const selectedDateEl = document.getElementById("selectedDate");
  const taskForm = document.getElementById("taskForm");
  const taskDateInput = document.getElementById("taskDate");
  const taskTitleInput = document.getElementById("taskTitle");
  const closeModalBtn = document.getElementById("closeModal");

  const editTaskModal = document.getElementById("editTaskModal");
  const editTaskForm = document.getElementById("editTaskForm");
  const editTaskIdInput = document.getElementById("editTaskId");
  const editTaskTitleInput = document.getElementById("editTaskTitle");
  const deleteTaskBtn = document.getElementById("deleteTaskBtn");
  const closeEditModalBtn = document.getElementById("closeEditModal");

  const csrftoken = getCookie("csrftoken");

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "dayGridMonth",
    selectable: true,
    headerToolbar: {
      left: "prev,next today",
      center: "title",
      right: "dayGridMonth,timeGridWeek,timeGridDay",
    },
    dateClick: function (info) {
      selectedDateEl.textContent = info.dateStr;
      taskDateInput.value = info.dateStr;
      taskTitleInput.value = "";
      taskModal.style.display = "block";
    },
    events: "/api/tasks/",

    eventClick: function (info) {
      const event = info.event;
      if (!event.id) {
        Toast.show("Error: Task without ID.", "error");
        return;
      }

      editTaskIdInput.value = event.id;
      editTaskTitleInput.value = event.title;
      editTaskModal.style.display = "block";
      editTaskModal.currentEvent = event;
    },
  });

  calendar.render();

  calendarEl.addEventListener("click", function (event) {
    const calendarApi = calendar;
    const eventEl = event.target.closest(".fc-event");

    if (!eventEl) return;

    const eventObj = calendarApi.getEventById(
      eventEl.getAttribute("data-event-id"),
    );
    if (!eventObj) return;

    editTaskIdInput.value = eventObj.id;
    editTaskTitleInput.value = eventObj.title;
    editTaskModal.style.display = "block";

    editTaskModal.currentEvent = eventObj;
  });

  editTaskForm.addEventListener("submit", function (e) {
    e.preventDefault();

    const id = editTaskIdInput.value.trim();
    const newTitle = editTaskTitleInput.value.trim();

    if (!id) {
      Toast.show("Missing task ID.", "error");
      return;
    }
    if (!newTitle) {
      Toast.show("Task title cannot be empty.", "error");
      return;
    }

    fetch(`/api/tasks/edit/${id}/`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
      },
      body: JSON.stringify({ title: newTitle }),
    })
      .then((res) => {
        if (res.ok) {
          editTaskModal.currentEvent.setProp("title", newTitle);
          editTaskModal.style.display = "none";
          Toast.show("Task updated!", "success");
        } else {
          Toast.show("Failed to update task.", "error");
        }
      })
      .catch(() => Toast.show("Network error.", "error"));
  });

  deleteTaskBtn.addEventListener("click", function () {
    const id = editTaskIdInput.value;

    if (confirm("Delete this task?")) {
      fetch(`/api/tasks/delete/${id}/`, {
        method: "DELETE",
        headers: { "X-CSRFToken": csrftoken },
      })
        .then((res) => {
          if (res.ok) {
            editTaskModal.currentEvent.remove();
            editTaskModal.style.display = "none";
            Toast.show("Task deleted.", "warning");
          } else {
            Toast.show("Failed to delete task.", "error");
          }
        })
        .catch(() => Toast.show("Network error.", "error"));
    }
  });

  closeEditModalBtn.addEventListener("click", () => {
    editTaskModal.style.display = "none";
  });

  taskForm.addEventListener("submit", function (e) {
    e.preventDefault();

    const title = taskTitleInput.value.trim();
    const date = taskDateInput.value;

    if (!title || !date) {
      Toast.show("Please fill in all fields.", "warning");
      return;
    }

    fetch("/api/tasks/add/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
      },
      body: JSON.stringify({ title: title, date: date }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === "success") {
          calendar.refetchEvents();
          taskModal.style.display = "none";
          Toast.show("Task added!", "success");
        } else {
          Toast.show("Error while adding task.", "error");
        }
      })
      .catch(() => Toast.show("Network error.", "error"));
  });

  closeModalBtn.addEventListener("click", () => {
    taskModal.style.display = "none";
  });
});
