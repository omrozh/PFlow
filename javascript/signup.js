referral = new URLSearchParams(window.location.search).get("referral");

window.addEventListener('DOMContentLoaded', (event) => {
    document.getElementById("referral_code").value = referral
});
