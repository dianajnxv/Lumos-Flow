document.addEventListener("DOMContentLoaded", function () {
  const themeButton = document.getElementById("theme-button");
  const dropdown = document.getElementById("dropdown");
  const buttons = document.querySelectorAll("#dropdown button");
  const logoImg = document.querySelector(".navbar-logo");

  console.log("Theme toggle script loaded. Button found:", !!themeButton);

  function applyTheme(theme) {
    document.body.classList.remove(
      "light-theme",
      "dark-theme",
      "motivational-theme",
    );
    document.body.classList.add(`${theme}-theme`);

    if (logoImg && logoImg.tagName === "IMG") {
      logoImg.src =
        theme === "dark"
          ? "/static/images/logo-white.png"
          : "/static/images/logo-black.png";
    }

    localStorage.setItem("selected-theme", theme);
  }

  if (themeButton && dropdown) {
    themeButton.onclick = function (e) {
      e.stopPropagation();
      const isVisible = dropdown.style.display === "block";
      dropdown.style.display = isVisible ? "none" : "block";
      console.log("Dropdown toggled to:", dropdown.style.display);
    };

    document.addEventListener("click", function (e) {
      if (!themeButton.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.style.display = "none";
      }
    });
  } else {
    console.warn("Theme button or dropdown missing in HTML!");
  }

  function sendThemeToServer(theme) {
    const csrftoken =
      document
        .querySelector('meta[name="csrf-token"]')
        ?.getAttribute("content") ||
      document.querySelector("[name=csrfmiddlewaretoken]")?.value;

    if (!csrftoken) {
      console.error("CSRF token not found!");
      Toast.show("Security error: Token missing", "error");
      return;
    }

    const formData = new URLSearchParams();
    formData.append("theme", theme);

    console.log("Attempting to send theme:", theme);

    fetch("/change-theme/", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRFToken": csrftoken,
      },
      body: formData.toString(),
    })
      .then((response) => {
        console.log("Server response status:", response.status);
        if (!response.ok) throw new Error("Server error " + response.status);
        return response.json();
      })
      .then((data) => {
        console.log("Success data:", data);

        if (data && data.status === "success") {
          Toast.show("Theme updated successfully!", "success");

          setTimeout(() => {
            location.reload();
          }, 2000);
        }
      })
      .catch((error) => {
        console.error("Full error details:", error);
        Toast.show("Sync failed: " + error.message, "error");
      });
  }

  buttons.forEach((button) => {
    button.addEventListener("click", function (e) {
      e.preventDefault();
      const theme = this.id.replace("-button", "");

      applyTheme(theme);
      sendThemeToServer(theme);

      dropdown.style.display = "none";
    });
  });

  const savedTheme = localStorage.getItem("selected-theme");
  if (savedTheme) {
    applyTheme(savedTheme);
  }

  document.addEventListener("mousemove", (e) => {
    const wrapper = document.querySelector(".magic-wrapper");
    if (wrapper) {
      const rect = wrapper.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      wrapper.style.setProperty("--x", `${x}px`);
      wrapper.style.setProperty("--y", `${y}px`);
    }
  });
});
