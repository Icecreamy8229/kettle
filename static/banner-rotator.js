document.addEventListener("DOMContentLoaded", function () {
    const videos = document.querySelectorAll('.banner-video');
    const titles = document.querySelectorAll('.video-info');
    let current = 0;

    function showVideo(index) {
        videos.forEach((video, i) => {

            if (i === index) {
            video.classList.add('active');
            titles[i].classList.add('active');
            video.currentTime = 0;
            video.play();

            } else {
            video.classList.remove('active');
            titles[i].classList.remove('active');
            video.pause();

            }

        });
  }

  // Start first video
  showVideo(current);

  videos.forEach((video, i) => {

      video.addEventListener('ended', () => {

          current = (i + 1) % videos.length;

          showVideo(current);

    });

  });

});