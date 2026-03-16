// Poll for new notifications
(function () {
    const badge = document.getElementById('notif-badge');
    if (!badge) return;

    function fetchNotifications() {
        fetch('/notifications/api')
            .then(r => r.json())
            .then(data => {
                if (data.length > 0) {
                    badge.textContent = data.length;
                    badge.classList.remove('d-none');
                } else {
                    badge.classList.add('d-none');
                }
            })
            .catch(() => {});
    }

    fetchNotifications();
    setInterval(fetchNotifications, 30000);
})();
