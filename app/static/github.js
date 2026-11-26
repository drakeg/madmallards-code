(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const input = $("github-repo");
  const status = $("github-status");
  const display = $("github-results");
  const action = $("github-load");

  function safeGithubLink(href, label) {
    const link = document.createElement("a");
    try {
      const url = new URL(href);
      if (url.protocol === "https:" && url.hostname === "github.com") {
        link.href = url.href;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
      }
    } catch (_) { /* untrusted URL is not linked */ }
    link.textContent = label;
    link.className = "link-info";
    return link;
  }
  function section(title) {
    const heading = document.createElement("div");
    heading.className = "sidebar-label mt-3 mb-2";
    heading.textContent = title;
    const container = document.createElement("div");
    container.className = "d-grid gap-2";
    display.append(heading, container);
    return container;
  }
  function item(container, content, summary) {
    const outer = document.createElement("div");
    outer.className = "small";
    outer.append(content);
    if (summary) {
      const detail = document.createElement("div");
      detail.className = "text-white-50";
      detail.textContent = summary;
      outer.append(detail);
    }
    container.append(outer);
  }
  async function load(event) {
    event?.preventDefault();
    const value = input.value.trim();
    if (!/^[A-Za-z0-9][A-Za-z0-9_-]{0,38}\/[A-Za-z0-9_.-]{1,100}$/.test(value)) {
      status.textContent = "Enter owner/repository.";
      return;
    }
    display.replaceChildren();
    action.disabled = true;
    status.textContent = "Checking public GitHub status…";
    try {
      const response = await fetch("/api/v1/github/" + value);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "GitHub lookup failed");
      const info = section("Repository");
      item(info, safeGithubLink(data.url, data.name), data.description);
      item(info, document.createTextNode("Default branch: " + data.default_branch), "Public repository · read only");

      const branches = section("Branches (" + data.branches.length + " shown)");
      if (!data.branches.length) item(branches, document.createTextNode("No branches returned"));
      for (const branch of data.branches) {
        item(branches, document.createTextNode(branch.name), branch.protected ? "Protected" : "");
      }
      const prs = section("Open PRs (" + data.pull_requests.length + " shown)");
      if (!data.pull_requests.length) item(prs, document.createTextNode("No open PRs"));
      for (const pr of data.pull_requests) {
        item(prs, safeGithubLink(pr.url, "#" + pr.number + " " + pr.title), pr.draft ? "Draft" : "Open");
      }
      const runs = section("Recent CI runs");
      if (!data.runs.length) item(runs, document.createTextNode("No runs returned"));
      for (const run of data.runs) {
        item(runs, safeGithubLink(run.url, run.name), (run.conclusion || run.status) + " · " + run.branch);
      }
      status.textContent = "Public GitHub data loaded. No permissions granted.";
    } catch (error) {
      status.textContent = error.message;
    } finally {
      action.disabled = false;
    }
  }
  $("github-form").addEventListener("submit", load);
})();
