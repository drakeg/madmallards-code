(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const state = { conversationId: null, busy: false, controller: null };
  const messages = $("messages"), prompt = $("prompt"), form = $("composer");
  const modelSelect = $("model-select");
  const status = $("connection-status");
  const send = $("send-button");

  function announce(message, isError = false) {
    status.textContent = message;
    status.className = isError ? "small text-danger" : "small text-secondary";
  }
  async function api(url, options = {}) {
    const response = await fetch(url, options);
    if (!response.ok) {
      let detail = "Request failed";
      try { detail = (await response.json()).detail || detail; } catch (_) { /* empty */ }
      throw new Error(detail);
    }
    return response;
  }
  function appendMessage(role, content = "") {
    $("empty-state").hidden = true;
    const el = document.createElement("article");
    el.className = "message " + (role === "user" ? "message-user" : "message-assistant");
    const heading = document.createElement("div");
    heading.className = "message-role";
    heading.textContent = role === "user" ? "You" : "Mad Mallards Code";
    const body = document.createElement("div");
    body.className = "message-text";
    body.textContent = content;
    el.append(heading, body);
    messages.appendChild(el);
    messages.scrollTop = messages.scrollHeight;
    return body;
  }
  async function loadConversations() {
    const data = await (await api("/api/v1/conversations")).json();
    const list = $("conversation-list");
    list.replaceChildren();
    for (const item of data.conversations) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "conversation-item btn btn-sm w-100 text-start " +
        (item.id === state.conversationId ? "active" : "");
      btn.textContent = item.title;
      btn.title = item.title;
      btn.addEventListener("click", () => openConversation(item.id));
      list.append(btn);
    }
    return data.conversations;
  }
  async function openConversation(id) {
    if (state.busy) return;
    state.conversationId = id;
    const data = await (await api("/api/v1/conversations/" + encodeURIComponent(id))).json();
    messages.querySelectorAll(".message").forEach((el) => el.remove());
    $("empty-state").hidden = data.messages.length > 0;
    $("conversation-title").textContent = data.title;
    data.messages.forEach((message) => appendMessage(message.role, message.content));
    await loadConversations();
    prompt.focus();
  }
  async function newConversation() {
    if (state.busy) return;
    const result = await (await api("/api/v1/conversations", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({title: "New conversation"})
    })).json();
    await openConversation(result.id);
  }
  async function loadModels() {
    const data = await (await api("/api/v1/models")).json();
    modelSelect.replaceChildren();
    for (const item of data.models) {
      const option = document.createElement("option");
      option.value = item.name;
      option.textContent = item.name;
      modelSelect.append(option);
    }
    send.disabled = data.models.length === 0;
    announce(data.models.length ? data.models.length + " local model(s) ready" :
      "Install a local model in Ollama to start chatting", !data.models.length);
  }
  function setBusy(busy) {
    state.busy = busy;
    prompt.disabled = busy;
    send.disabled = busy || !modelSelect.value;
    modelSelect.disabled = busy;
    $("new-chat").disabled = busy;
    $("cancel-button").hidden = !busy;
  }
  async function submit(event) {
    event.preventDefault();
    const question = prompt.value.trim();
    if (!question || state.busy || !modelSelect.value) return;
    setBusy(true);
    const controller = new AbortController();
    state.controller = controller;
    let reply;
    try {
      if (!state.conversationId) {
        const result = await (await api("/api/v1/conversations", {
          method: "POST", headers: {"Content-Type": "application/json"},
          body: JSON.stringify({title: "New conversation"})
        })).json();
        state.conversationId = result.id;
      }
      appendMessage("user", question);
      prompt.value = "";
      reply = appendMessage("assistant", "");
      announce("Generating response…");
      const response = await api("/api/v1/conversations/" + encodeURIComponent(state.conversationId) + "/messages", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({model: modelSelect.value, prompt: question}),
        signal: controller.signal
      });
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "", complete = false;
      while (!complete) {
        const chunk = await reader.read();
        if (chunk.done) break;
        buffer += decoder.decode(chunk.value, {stream:true});
        const lines = buffer.split("\n");
        buffer = lines.pop();
        for (const line of lines) {
          if (!line.trim()) continue;
          const item = JSON.parse(line);
          if (item.type === "token") {
            reply.textContent += item.content;
            messages.scrollTop = messages.scrollHeight;
          } else if (item.type === "error") {
            throw new Error(item.message);
          } else if (item.type === "done") {
            complete = true;
          }
        }
      }
      if (!complete) throw new Error("Model stream ended unexpectedly");
      announce("Response complete");
    } catch (error) {
      if (reply) reply.textContent += "\n" +
        (error.name === "AbortError" ? "Response cancelled." : "Error: " + error.message);
      announce(error.name === "AbortError" ? "Cancelled" : error.message, error.name !== "AbortError");
    } finally {
      state.controller = null;
      setBusy(false);
      try { await loadConversations(); } catch (_) { /* retains chat */ }
      prompt.focus();
    }
  }

  form.addEventListener("submit", submit);
  $("new-chat").addEventListener("click", () => newConversation().catch((err) => announce(err.message, true)));
  $("cancel-button").addEventListener("click", () => state.controller?.abort());
  prompt.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      form.requestSubmit();
    }
  });
  (async () => {
    try {
      await loadModels();
      const items = await loadConversations();
      if (items.length) await openConversation(items[0].id);
    } catch (error) { announce(error.message, true); }
  })();
})();
