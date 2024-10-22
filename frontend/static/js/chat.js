document.addEventListener("DOMContentLoaded", function () {
  const chatMessages = document.getElementById("chat-messages");
  const messageInput = document.getElementById("message-input");
  const sendButton = document.getElementById("send-button");
  const disconnectButton = document.getElementById("disconnect-button");
  const peerInfoContainer = document.getElementById("peer-info");

  let receivedMessages = new Set();
  let expandedCards = new Set();
  let pollingInterval;

  updateUserInfo();
  updatePeerInfo();
  fetchMessages();

  pollingInterval = setInterval(() => {
    fetchMessages();
    updatePeerInfo();
  }, 3000);

  window.toggleCard = function (nickname) {
    const content = document.getElementById(`content-${nickname}`);
    const chevron = content.previousElementSibling.querySelector(".chevron");

    if (content.classList.contains("expanded")) {
      content.classList.remove("expanded");
      chevron.classList.remove("expanded");
      expandedCards.delete(nickname); // close
    } else {
      content.classList.add("expanded");
      chevron.classList.add("expanded");
      expandedCards.add(nickname); // open
    }
  };

  function updateUserInfo() {
    fetch("/get_client_info/")
      .then((response) => response.json())
      .then((data) => {
        document.getElementById("user-nickname").textContent = data.nickname;
        if (data.client_address) {
          document.getElementById("user-ip").textContent =
            data.client_address.ip;
          document.getElementById("user-port").textContent =
            data.client_address.port;
        }
        if (data.server_connection) {
          console.log("Server IP:", data.server_connection.ip);
          console.log("Server Port:", data.server_connection.port);
        }
      })
      .catch((error) => {
        console.error("No client info", error);
      });
  }

  function updatePeerInfo() {
    fetch("/get_peer_info/")
      .then((response) => response.json())
      .then((data) => {
        peerInfoContainer.innerHTML = "";

        for (const [nickname, info] of Object.entries(data)) {
          const card = document.createElement("div");
          card.className = `peer-card ${
            info.status === "オンライン" ? "online" : "offline"
          }`;
          card.id = `peer-${nickname}`;

          const safeNickname = escapeHtml(nickname);

          card.innerHTML = `
            <button class="peer-card-header" onclick="toggleCard('${safeNickname}')">
              <span class="peer-nickname">${safeNickname}</span>
              <svg class="chevron ${
                expandedCards.has(nickname) ? "expanded" : ""
              }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 9l6 6 6-6" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <div class="peer-card-content ${
              expandedCards.has(nickname) ? "expanded" : ""
            }" id="content-${safeNickname}">
              <p class="peer-info-item">IP: ${escapeHtml(info.ip)}</p>
              <p class="peer-info-item">Port: ${escapeHtml(info.port)}</p>
              <p class="peer-info-item">
                <span class="status-badge ${
                  info.status === "オンライン" ? "online" : "offline"
                }">
                  ${escapeHtml(info.status)}
                </span>
              </p>
            </div>
          `;

          peerInfoContainer.appendChild(card);
        }
      })
      .catch((error) => {
        console.error("ピア情報の更新に失敗:", error);
      });
  }

  function fetchMessages() {
    fetch("/get_messages/")
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        if (data && Array.isArray(data.messages)) {
          const newMessages = data.messages
            .map((msg) => {
              return typeof msg === "string" ? JSON.parse(msg) : msg;
            })
            .filter(
              (message) => !receivedMessages.has(JSON.stringify(message))
            );

          if (newMessages.length > 0) {
            displayMessages(newMessages);
            newMessages.forEach((message) =>
              receivedMessages.add(JSON.stringify(message))
            );
          }
        } else {
          console.error("予期しないデータ形式:", data);
        }
      })
      .catch((error) => console.error("メッセージ取得エラー:", error));
  }

  function sendMessage() {
    const message = messageInput.value.trim();
    if (message) {
      fetch("/send_message/", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": getCookie("csrftoken"),
        },
        body: `message=${encodeURIComponent(message)}`,
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.status === "success") {
            messageInput.value = "";
            fetchMessages();
          }
        });
    }
  }

  function displayMessages(messages) {
    messages.forEach((message) => {
      if (!message || !message.username || !message.content) {
        console.error("Invalid message format:", message);
        return;
      }

      const messageElement = document.createElement("div");
      messageElement.classList.add("message");

      const { fullTimestamp, timeOnly } = getCurrentTimestamp();
      const username = escapeHtml(message.username);
      const content = escapeHtml(message.content);

      messageElement.innerHTML = `
        <div class="message-header">
          <strong>${username}</strong>
          <time datetime="${fullTimestamp}" title="${fullTimestamp}">${timeOnly}</time>
        </div>
        <div class="message-content">
          ${content}
        </div>
      `;

      chatMessages.appendChild(messageElement);
    });

    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function getCurrentTimestamp() {
    const now = new Date();
    const fullTimestamp = now.toISOString().replace("T", " ").slice(0, 19);
    const timeOnly = now.toTimeString().slice(0, 5);
    return { fullTimestamp, timeOnly };
  }

  function escapeHtml(unsafe) {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
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

  function disconnect() {
    fetch("/disconnect/", {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.status === "success") {
          if (pollingInterval) {
            clearInterval(pollingInterval);
          }
          window.location.href = "/";
        }
      });
  }

  sendButton.addEventListener("click", sendMessage);
  messageInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      sendMessage();
    }
  });
  disconnectButton.addEventListener("click", disconnect);
});
