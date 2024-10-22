document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("connect-form");

  function saveFormValues() {
    const formData = {
      nickname: document.getElementById("nickname").value,
      ip_address: document.getElementById("ip_address").value,
      port: document.getElementById("port").value,
    };
    localStorage.setItem("connectionFormData", JSON.stringify(formData));
  }

  function restoreFormValues() {
    const savedData = localStorage.getItem("connectionFormData");
    if (savedData) {
      const formData = JSON.parse(savedData);
      document.getElementById("nickname").value = formData.nickname || "";
      document.getElementById("ip_address").value = formData.ip_address || "";
      document.getElementById("port").value = formData.port || "";
    }
  }

  restoreFormValues();

  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      const submitButton = form.querySelector('button[type="submit"]');
      submitButton.textContent = "Connecting...";
      submitButton.disabled = true;

      saveFormValues();

      fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },
      })
        .then((response) => {
          if (response.ok) {
            window.location.href = "/chat/";
          } else {
            return response.json();
          }
        })
        .then((data) => {
          if (data && data.error) {
            showError(data.error);
          }
        })
        .catch((error) => {
          showError("エラーが発生しました。もう一度お試しください。");
        })
        .finally(() => {
          submitButton.textContent = "Connect";
          submitButton.disabled = false;
        });
    });
  }

  function showError(message) {
    let errorDiv = document.querySelector(".error-message");
    if (!errorDiv) {
      errorDiv = document.createElement("div");
      errorDiv.className = "error-message";
      form.appendChild(errorDiv);
    }
    errorDiv.textContent = message;
    errorDiv.style.opacity = "0";
    requestAnimationFrame(() => {
      errorDiv.style.transition = "opacity 0.3s ease-in";
      errorDiv.style.opacity = "1";
    });
  }

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
});
