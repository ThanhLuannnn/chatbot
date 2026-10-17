const input = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const messages = document.getElementById("messages");
const welcome = document.getElementById("welcome");
const apiStatus = document.getElementById("apiStatus");
let history = [];
let busy = false;

function resizeInput() {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 150) + "px";
}
input.addEventListener("input", resizeInput);
input.addEventListener("keydown", event => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
});
document.getElementById("newChat").addEventListener("click", () => {
  history = [];
  messages.innerHTML = "";
  welcome.style.display = "";
  input.value = "";
  resizeInput();
  input.focus();
});
document.querySelectorAll("[data-prompt]").forEach(button => {
  button.addEventListener("click", () => {
    input.value = button.dataset.prompt;
    resizeInput();
    sendMessage();
  });
});

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    apiStatus.textContent = data.api_configured ? "CONNECTED" : "SETUP NEEDED";
    apiStatus.style.color = data.api_configured ? "var(--green)" : "#ffbd73";
  } catch {
    apiStatus.textContent = "OFFLINE";
    apiStatus.style.color = "#ff9c8b";
  }
}
function addMessage(role, content, extraClass = "") {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;
  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = role === "assistant" ? "✳" : "U";
  const body = document.createElement("div");
  body.className = "msg-body";
  const name = document.createElement("div");
  name.className = "msg-name";
  name.textContent = role === "assistant" ? "NEURAL AGENT" : "YOU";
  const text = document.createElement("div");
  text.className = `msg-text ${extraClass}`;
  text.textContent = content;
  body.append(name, text);
  wrapper.append(avatar, body);
  messages.appendChild(wrapper);
  const scroller = document.getElementById("content");
  scroller.scrollTop = scroller.scrollHeight;
  return text;
}
async function sendMessage() {
  const message = input.value.trim();
  if (!message || busy) return;
  busy = true;
  sendButton.disabled = true;
  welcome.style.display = "none";
  addMessage("user", message);
  input.value = "";
  resizeInput();
  const pending = addMessage("assistant", "Đang phân tích nhiệm vụ và lựa chọn công cụ phù hợp…", "typing");
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message, history})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Yêu cầu thất bại.");
    pending.classList.remove("typing");
    pending.textContent = data.reply;
    history.push({role: "user", content: message}, {role: "assistant", content: data.reply});
    history = history.slice(-24);
    await checkHealth();
  } catch (error) {
    pending.classList.remove("typing");
    pending.classList.add("error");
    pending.textContent = "Kết nối thất bại: " + error.message;
  } finally {
    busy = false;
    sendButton.disabled = false;
    input.focus();
    const scroller = document.getElementById("content");
    scroller.scrollTop = scroller.scrollHeight;
  }
}
sendButton.addEventListener("click", sendMessage);
checkHealth();
