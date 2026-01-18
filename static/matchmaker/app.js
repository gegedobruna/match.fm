(() => {
  const startMatchPolling = () => {
    const statusUrl = document.body?.dataset?.statusUrl;
    if (!statusUrl) return;

    const refreshMs = Number(document.body.dataset.refreshMs || 1500) || 1500;

    const checkStatus = () => {
      fetch(statusUrl, { headers: { Accept: "application/json" } })
        .then((r) => r.json())
        .then((data) => {
          if (data.status === "READY" && data.redirect) {
            window.location = data.redirect;
          } else if (data.status === "FAILED") {
            window.location.reload();
          }
        })
        .catch(() => {});
    };

    checkStatus();
    setInterval(checkStatus, refreshMs);
  };

  const setupCopyLink = () => {
    const btn = document.querySelector("[data-copy-link]");
    if (!btn || !navigator?.clipboard) return;

    btn.addEventListener("click", () => {
      navigator.clipboard.writeText(window.location.href).catch(() => {});
    });
  };

  window.addEventListener("DOMContentLoaded", () => {
    setupCopyLink();
    startMatchPolling();
  });
})();
