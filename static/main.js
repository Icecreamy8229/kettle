document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM fully loaded and parsed");

    let flashMessages = document.querySelectorAll(".flash-msg");
    console.log(flashMessages.length);

    if (flashMessages.length > 0) {
        setTimeout(() => {
            flashMessages.forEach(message => {
                if (message.classList.contains("alert-success")) {
                    console.log(message.textContent);
                    message.style.opacity = "0";
                    setTimeout(() => message.remove(), 1000); // Remove after fade-out

                }
                            });
        }, 3000); // Wait 3 seconds before fading out

    }

});