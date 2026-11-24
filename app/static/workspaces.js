(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const select = $("workspace-select");
  const tree = $("workspace-tree");
  const status = $("file-browser-status");
  let selectedContext = null;
  const pathLabel = $("workspace-path");

  async function get(url) {
    const response = await fetch(url);
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || "Workspace request failed");
    }
    return response.json();
  }
  function showError(error) {
    status.textContent = error.message;
  }
  function entryButton(label, handler, symbol) {
    const entry = document.createElement("button");
    entry.type = "button";
    entry.className = "btn btn-sm text-start text-light";
    entry.textContent = symbol + " " + label;
    entry.addEventListener("click", () => handler().catch(showError));
    return entry;
  }
  async function showFile(path) {
    const data = await get("/api/v1/workspaces/" + encodeURIComponent(select.value)
      + "/file?path=" + encodeURIComponent(path));
    $("preview-title").textContent = select.value + " / " + data.path;
    $("preview-code").textContent = data.content;
    $("file-preview").hidden = false;
    $("attach-context").hidden = false;
    $("attach-context").disabled = false;
    $("attach-context").textContent = "Attach to next question";
    $("attach-context").dataset.workspace = select.value;
    $("attach-context").dataset.path = path;
    status.textContent = "Previewing " + path;
  }
  async function browse(path = "") {
    const workspace = select.value;
    tree.replaceChildren();
    pathLabel.textContent = workspace ? "/" + workspace + (path ? "/" + path : "") : "";
    if (!workspace) return;
    const data = await get("/api/v1/workspaces/" + encodeURIComponent(workspace)
      + "/tree?path=" + encodeURIComponent(path));
    if (path) {
      const up = path.includes("/") ? path.slice(0, path.lastIndexOf("/")) : "";
      tree.append(entryButton(".. (up)", () => browse(up), "↑"));
    }
    for (const entry of data.entries) {
      const next = path ? path + "/" + entry.name : entry.name;
      tree.append(entry.kind === "directory"
        ? entryButton(entry.name + "/", () => browse(next), "▸")
        : entryButton(entry.name, () => showFile(next), "·"));
    }
    status.textContent = data.entries.length + " entries";
  }
  async function initialize() {
    const data = await get("/api/v1/workspaces");
    select.replaceChildren();
    if (!data.workspaces.length) {
      const empty = document.createElement("option");
      empty.value = "";
      empty.textContent = "No workspaces mounted";
      select.append(empty);
      status.textContent = "Place repos in workspaces/ on the host";
      return;
    }
    for (const item of data.workspaces) {
      const option = document.createElement("option");
      option.value = item.name;
      option.textContent = item.name;
      select.append(option);
    }
    await browse();
  }
  select.addEventListener("change", () => browse("").catch(showError));
  $("close-preview").addEventListener("click", () => { $("file-preview").hidden = true; });
  $("attach-context").addEventListener("click", () => {
    selectedContext = {
      workspace: $("attach-context").dataset.workspace,
      path: $("attach-context").dataset.path
    };
    $("selected-file-context").textContent = "Attached: " + selectedContext.workspace + "/" + selectedContext.path;
    $("remove-file-context").hidden = false;
  });
  $("remove-file-context").addEventListener("click", () => {
    selectedContext = null;
    $("selected-file-context").textContent = "";
    $("remove-file-context").hidden = true;
  });
  window.MMCContext = {
    consume() {
      const value = selectedContext;
      selectedContext = null;
      $("selected-file-context").textContent = "";
      $("remove-file-context").hidden = true;
      return value;
    },
    peek() { return selectedContext; }
  };
  initialize().catch(showError);
})();
