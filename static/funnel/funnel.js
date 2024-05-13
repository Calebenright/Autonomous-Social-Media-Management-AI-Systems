document.addEventListener("DOMContentLoaded", function() {
    var videoPlaceholders = document.querySelectorAll('.youtube-video-placeholder');

    videoPlaceholders.forEach(function(placeholder) {
        placeholder.addEventListener('click', function() {
            // Create the iframe
            var iframe = document.createElement('iframe');
            iframe.setAttribute('src', placeholder.getAttribute('data-embed') + "&autoplay=1");
            iframe.setAttribute('frameborder', '0');
            iframe.setAttribute('allowfullscreen', 'true');
            iframe.setAttribute('allow', 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share');
            iframe.classList.add('rounded', 'shadow-l', 'video-player');

            placeholder.replaceWith(iframe);
        }, { once: true }); 
    });
});
