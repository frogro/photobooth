// FIXED payment_poll.js

(function () {
    let pollTimer = null;

    function startPolling() {
        stopPolling();

        pollTimer = setInterval(() => {
            $.ajax({
                url: '/api/paymentStatus.php',
                method: 'GET',
                dataType: 'json',
                success: function (data) {
                    if (data.paid && data.printed) {
                        stopPolling();

                        if (typeof window.photoboothTools !== 'undefined') {
                            window.photoboothTools.isPrinting = false;
                        }
                    }
                }
            });
        }, 2000);
    }

    function stopPolling() {
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
    }

    const observer = new MutationObserver(() => {
        const overlay = document.querySelector('.overlay');

        if (!overlay) return;

        if (
            overlay.classList.contains('overlay-qr') ||
            overlay.classList.contains('overlay-both') ||
            overlay.classList.contains('overlay-coin')
        ) {
            startPolling();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
})();
