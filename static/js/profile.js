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
      const isAjax = false;
      if (isAjax) {
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
            window.location.reload();
          }
        } catch (error) {
          console.error("Error:", error);
        }
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
