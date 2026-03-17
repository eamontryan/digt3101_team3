// Appointment scheduling helpers
document.addEventListener('DOMContentLoaded', function () {
    const startInput = document.querySelector('input[name="date_time"]');
    const endInput = document.querySelector('input[name="end_time"]');

    if (startInput && endInput) {
        startInput.addEventListener('change', function () {
            // Auto-set end time to 1 hour after start
            const start = new Date(this.value);
            if (!isNaN(start.getTime())) {
                start.setHours(start.getHours() + 1);
                const pad = n => String(n).padStart(2, '0');
                const endVal = `${start.getFullYear()}-${pad(start.getMonth() + 1)}-${pad(start.getDate())}T${pad(start.getHours())}:${pad(start.getMinutes())}`;
                endInput.value = endVal;
            }
        });
    }
});