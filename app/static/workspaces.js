(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const select = $("workspace-select");
  const tree = $("workspace-tree");
  const status = $("file-browser-status");
  let selectedContext = null;
  const pathLabel = $("workspace-path");
  let currentFile = null;
  let reviewedDiff = "";

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
    currentFile = data;
    reviewedDiff = "";
    $("download-proposal-patch").hidden = true;
    $("proposal-content").value = data.content;
    $("proposal-diff").textContent = "";
    $("proposal-diff").hidden = true;
    $("proposal-status").textContent = "";
    $("proposal-panel").open = false;
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
    currentFile = null;
    reviewedDiff = "";
    $("download-proposal-patch").hidden = true;
    $("file-preview").hidden = true;
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
  $("ai-preview-proposal").addEventListener("click", async () => {
    if (!currentFile) return;
    const instruction = $("ai-change-request").value.trim();
    const model = $("model-select").value;
    if (!instruction || !model) {
      $("proposal-status").textContent = "Select a local model and describe your requested change.";
      return;
    }
    const button = $("ai-preview-proposal");
    button.disabled = true;
    $("proposal-status").textContent = "Generating a read-only proposal…";
    try {
      const response = await fetch("/api/v1/workspaces/" +
        encodeURIComponent(currentFile.workspace) + "/ai-proposal", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          path: currentFile.path, baseline_sha256: currentFile.sha256,
          instruction, model
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Model proposal failed");
      $("proposal-content").value = data.proposed_content;
      reviewedDiff = data.diff || "";
      $("download-proposal-patch").hidden = !reviewedDiff;
      $("proposal-diff").textContent = reviewedDiff || "No changes";
      $("proposal-diff").hidden = false;
      $("proposal-status").textContent = "Review generated diff. No file was modified.";
    } catch (error) {
      reviewedDiff = "";
      $("download-proposal-patch").hidden = true;
      $("proposal-status").textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
  $("preview-proposal").addEventListener("click", async () => {
    if (!currentFile) return;
    $("proposal-status").textContent = "Building read-only diff…";
    try {
      const response = await fetch("/api/v1/workspaces/" +
        encodeURIComponent(currentFile.workspace) + "/proposals", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          path: currentFile.path,
          baseline_sha256: currentFile.sha256,
          proposed_content: $("proposal-content").value
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Unable to preview changes");
      reviewedDiff = data.diff || "";
      $("download-proposal-patch").hidden = !reviewedDiff;
      $("proposal-diff").textContent = reviewedDiff || "No changes";
      $("proposal-diff").hidden = false;
      $("proposal-status").textContent = "Preview only — no file was modified.";
    } catch (error) {
      reviewedDiff = "";
      $("download-proposal-patch").hidden = true;
      $("proposal-status").textContent = error.message;
    }
  });
  $("download-proposal-patch").addEventListener("click", () => {
    if (!currentFile || !reviewedDiff) return;
    const filename = (currentFile.workspace + "_" + currentFile.path)
      .replace(/[^a-zA-Z0-9._-]/g, "_") + ".patch";
    const blob = new Blob([reviewedDiff], {type: "text/x-patch;charset=utf-8"});
    const href = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = href;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(href), 1000);
    $("proposal-status").textContent = "Patch downloaded. Review and validate before applying it manually.";
  });
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
