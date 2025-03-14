let currentIndex = 0;
const transitionSpeed = "200ms";
document.addEventListener('DOMContentLoaded', () => {

    const slideButtons = document.querySelectorAll('.slide-button');
    const items = document.querySelectorAll('.slide');
    items[0].classList.add('active');
    slideButtons[0].classList.add('active');


})
function moveToSlide(index) {
    const slideButtons = document.querySelectorAll('.slide-button');
    const items = document.querySelectorAll('.slide');
    const totalSlides = items.length;

    if (totalSlides === 0 || index < 0 || index >= totalSlides) return; //this is a failsafe.  just an early return if the index is outside of the realm of possibility

    // Remove active class from slide and button
    items[currentIndex].classList.remove('active');
    slideButtons[currentIndex].classList.remove('active');


    let previousIndex = currentIndex; //saves previous index
    currentIndex = index;

    // Add active class to the new slide
    items[currentIndex].classList.add('active');
    slideButtons[currentIndex].classList.add('active');

    // Reset animation to re-trigger it
    const activeSlide = items[currentIndex];
    activeSlide.style.animation = 'none'; // Reset animation
    void activeSlide.offsetWidth; // Force reflow
    activeSlide.style.animation = previousIndex < currentIndex ? 'easeInFromRight ' + transitionSpeed : 'easeInFromLeft ' + transitionSpeed;
    //if previous index is less than current index, ease from the right, otherwise, ease from the left.

}


function moveSlide(step) {
    const items = document.querySelectorAll('.slide');
    const slideButtons = document.querySelectorAll('.slide-button');
    const totalSlides = items.length;

    if (totalSlides === 0) return; // Prevent errors if no slides exist

    // Remove active class from the current slide
    items[currentIndex].classList.remove('active');
    slideButtons[currentIndex].classList.remove('active');

    // Update the index
    currentIndex = (currentIndex + step + totalSlides) % totalSlides;

    // Add active class to the new slide
    items[currentIndex].classList.add('active');
    slideButtons[currentIndex].classList.add('active');

    // Reset animation to re-trigger it
    const activeSlide = items[currentIndex];
    activeSlide.style.animation = 'none'; // Reset
    void activeSlide.offsetWidth; // Force reflow
    activeSlide.style.animation = step < 0 ? 'easeInFromLeft ' + transitionSpeed : 'easeInFromRight ' + transitionSpeed;
}