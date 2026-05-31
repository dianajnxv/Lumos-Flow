document.addEventListener("DOMContentLoaded", function () {
  const getCookie = (name) => {
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
  };

  const editForm = document.querySelector("#editProfile form");
  if (editForm) {
    editForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      const formData = new FormData(editForm);
      try {
        const response = await fetch(editForm.action, {
          method: "POST",
          headers: { "X-CSRFToken": getCookie("csrftoken") },
          body: formData,
        });
        const result = await response.json();
        if (result.status === "success") {
          Toast.show("Profile updated!", "success");
          window.location.reload();
        } else {
          Toast.show(
            result.username_error ||
              result.bio_error ||
              result.avatar_error ||
              "Update failed.",
            "error",
          );
        }
      } catch (error) {
        Toast.show("Something went wrong.", "error");
      }
    });
  }

  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "bottom",
        labels: { boxWidth: 10, font: { size: 10 }, usePointStyle: true },
      },
    },
  };
});
