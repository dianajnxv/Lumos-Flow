document.addEventListener("show.bs.modal", function (event) {
  if (event.target.id === "modalSummary") {
    const nameInput = document.getElementById("recipient-name");
    const categoryInput = document.getElementById("message-text");
    const priorityInput = document.getElementById("priority-input");
    const finalNameInput = document.getElementById("final-name");
    const finalCategoryInput = document.getElementById("final-category");
    const finalPriorityInput = document.getElementById("final-priority");

    finalNameInput.value = nameInput ? nameInput.value : "";

    finalCategoryInput.value = categoryInput ? categoryInput.value : "";

    finalPriorityInput.value = priorityInput ? priorityInput.value : "";

    const days = [
      "Monday",
      "Tuesday",
      "Wednesday",
      "Thursday",
      "Friday",
      "Saturday",
      "Sunday",
    ];
    days.forEach((day) => {
      const originalCheckbox = document.getElementById(day);
      const finalCheckbox = document.getElementById(`final-${day}`);
      if (originalCheckbox && finalCheckbox) {
        finalCheckbox.checked = originalCheckbox.checked;
      }
    });
  }
});

document
  .getElementById("finalForm")
  .addEventListener("submit", async function (event) {
    event.preventDefault();

    const name = document.getElementById("final-name").value;
    const category = document.getElementById("final-category").value;
    const days = Array.from(
      document.querySelectorAll("#final-days input:checked"),
    ).map((input) => input.id.replace("final-", "").toLowerCase());
    const priority = document.getElementById("final-priority").value;

    try {
      const response = await fetch("habits/create_habit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: JSON.stringify({ name, category, days, priority }),
      });

      const result = await response.json();
      if (result.success) {
        Toast.show("Habit created successfully!", "success");
        const modal = bootstrap.Modal.getInstance(
          document.getElementById("modalSummary"),
        );
        modal.hide();
      } else {
        Toast.show(result.error || "Failed to create habit.", "error");
      }
    } catch (error) {
      console.error("Error:", error);
      Toast.show("Failed to create habit. Please try again.", "error");
    }
  });

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
