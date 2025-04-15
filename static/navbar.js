document.addEventListener('click', (e) => {
    const toggle = document.querySelector('.navbar-toggle');
    const links = document.querySelector('.links.collapsible');
    if (toggle.contains(e.target)) {
        links.classList.toggle('active');
    } else if (!links.contains(e.target)) {
        links.classList.remove('active');
    }
});

