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

            const scenario =
                new URLSearchParams(window.location.search).get("scenario") ||
                sessionStorage.getItem("scenario");


            if (scenario === "business-error") {
                result.innerHTML = `
                    <h2>INSUFFICIENT FUNDS</h2>
                    <p>Available balance: <strong>$100</strong></p>
                    <p>Requested: <strong>$${amount}</strong></p>
                `;
                return;
            }

            if (scenario === "hard-failure") {
                result.innerHTML = `
                    <h2>PERMISSION DENIED</h2>
                    <p>You are not authorized to submit this payment.</p>
                `;
                return;
            }

            if (scenario === "recoverable-error") {
                const alreadyFailed = sessionStorage.getItem(
                    "recoverable-error-shown"
                );

                if (!alreadyFailed) {
                    sessionStorage.setItem(
                        "recoverable-error-shown",
                        "true"
                    );

                    result.innerHTML = `
                        <h2>SERVICE TEMPORARILY UNAVAILABLE</h2>
                        <p>Please try again.</p>
                    `;

                    return;
                }
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
