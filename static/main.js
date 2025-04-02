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


function typeText(speed) {
    const typingSpeed = speed;
    const texts = Array.from(document.querySelectorAll('.type-text')).map(el => el.textContent);
    const elements = document.querySelectorAll(".type-text");

    // Clears existing text
    elements.forEach(element => {
        element.textContent = "";
    });

    let currentIndex = 0;

    function typeNextElement() {
        if (currentIndex >= elements.length) return; // Stop if all elements are processed


        const element = elements[currentIndex];
        const textToType = texts[currentIndex];

        element.style.visibility = "visible";

        const cursorSpan = document.createElement("span");
        cursorSpan.id = "cursor";

        if (document.getElementById("cursor")) {
            document.getElementById("cursor").remove();

        }

        element.appendChild(cursorSpan);

        let charIndex = 0;

        const typeInterval = setInterval(() => {
            if (charIndex < textToType.length) {
                cursorSpan.remove(); // Remove cursor
                element.innerHTML += textToType.charAt(charIndex); // Type character
                charIndex++;
                element.appendChild(cursorSpan); // Re-add cursor
            } else {
                clearInterval(typeInterval);

                currentIndex++; // Move to the next element
                typeNextElement(); // Start typing the next element, recursive call to itself.
            }
        }, typingSpeed);
    }

    typeNextElement(); // Start typing the first element
}
