// Dynamic search filtering for store units
document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form[action*="search"]');
    if (!form) return;

    const inputs = form.querySelectorAll('select, input[type="number"]');
    inputs.forEach(input => {
        input.addEventListener('change', function () {
            form.submit();
        });
    });
});