// Minimal mock banking behavior for the computer-use assignment.
// This is intentionally a frontend-only application. There is no real bank backend.

document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("loginForm");

    if (loginForm) {
        loginForm.addEventListener("submit", function (event) {
            event.preventDefault();

            const username = document.getElementById("username").value.trim();
            const password = document.getElementById("password").value;

            if (!username || !password) {
                document.getElementById("loginError").textContent =
                    "Username and password are required.";
                return;
            }

            // Fake login for the local demo only.
            // No real credentials are used or stored.
            window.location.href = "dashboard.html";
        });
    }

    const paymentForm = document.getElementById("paymentForm");

    if (paymentForm) {
        paymentForm.addEventListener("submit", function (event) {
            event.preventDefault();

            const fromAccount = document.getElementById("fromAccount").value.trim();
            const toAccount = document.getElementById("toAccount").value.trim();
            const amount = Number(document.getElementById("amount").value);
            const result = document.getElementById("result");

            if (!fromAccount || !toAccount || !amount || amount <= 0) {
                result.innerHTML = "<p role='alert'>Please enter valid payment details.</p>";
                return;
            }

            const transactionId = "TXN-" + Date.now();

            result.innerHTML = `
                <h2>PAYMENT SUCCESSFUL</h2>
                <p>Transaction ID: <strong>${transactionId}</strong></p>
                <p>Status: <strong>COMPLETED</strong></p>
            `;
        });
    }
});
