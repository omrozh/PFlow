short_login = new URLSearchParams(window.location.search).get("short_login");

window.addEventListener('DOMContentLoaded', (event) => {
    document.getElementById("short_login").value = short_login
});
