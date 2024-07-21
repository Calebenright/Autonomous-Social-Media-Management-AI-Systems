
0 < $('[data-plugins="dropify"]').length && $('[data-plugins="dropify"]').dropify({
    messages: {
        default: "File Upload",
        replace: "Replace File",
        remove: "Remove",
        error: "Ooops, something wrong appended."
    },
    error: {
        fileSize: "The file size is too big (1M max)."
    }
});

function showSpinner() {
    var form = document.querySelector('form');
    if (form.checkValidity()) {
        var loadingOverlay = document.getElementById('loading-overlay');
        var submitButton = document.querySelector('#myForm button[type="submit"]');
        loadingOverlay.style.display = 'flex';
        submitButton.disabled = true;
        var spinnerDuration = 5000;
        setTimeout(function() {
            loadingOverlay.style.display = 'none';
            submitButton.disabled = false;
        }, spinnerDuration);
    }
}

function showPopup(popupId) {
    document.getElementById(popupId).style.display = "block";
}

function hidePopup(popupId) {
    document.getElementById(popupId).style.display = "none";
}

function redirectToCheckout() {
    window.location.href = upgradeCheckout;
}

function cancelRequest() {
    document.getElementById('clearForm').submit();
    showSpinner();
}
    
const input = document.getElementById('files');
const thumbnailsContainer = document.getElementById('thumbnails-container');
const videoUploadOverlay = document.getElementById('video-upload-overlay');
const progressBar = document.getElementById('video-upload-progress-bar');

input.addEventListener('change', function () {
    const files = input.files;
    if (files.length > 0) {
        const file = files[0];

        // Show preview
        const previewDiv = document.createElement('div');
        previewDiv.classList.add('col-lg-6');
        if (file.type.startsWith('image/')) {
            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);
            img.style.width = '100%';
            img.style.height = 'auto';
            img.classList.add('rounded');
            img.classList.add('mt-2');
            previewDiv.appendChild(img);
        } else if (file.type.startsWith('video/')) {
            const video = document.createElement('video');
            video.src = URL.createObjectURL(file);
            video.style.width = '100%';
            video.style.height = 'auto';
            video.classList.add('rounded');
            video.classList.add('mt-2');
            video.controls = true;
            previewDiv.appendChild(video);
        }
        thumbnailsContainer.appendChild(previewDiv);

        const formData = new FormData();
        formData.append('file_name', file.name);
        formData.append('csrfmiddlewaretoken', '{{ csrf_token }}');

        fetch(sendForm, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.url) {
                videoUploadOverlay.style.display = 'block';
                const xhr = new XMLHttpRequest();
                xhr.open('PUT', data.url, true);
                xhr.setRequestHeader('Content-Type', 'application/octet-stream');

                xhr.upload.addEventListener('progress', function (event) {
                    if (event.lengthComputable) {
                        const percentComplete = (event.loaded / event.total) * 100;
                        progressBar.style.width = percentComplete + '%';
                    }
                });

                xhr.addEventListener('load', function () {
                    videoUploadOverlay.style.display = 'none';
                    if (xhr.status === 200) {
                        // Optionally update the preview or show success message
                    } else {
                        alert('File upload failed.');
                    }
                });

                xhr.addEventListener('error', function () {
                    console.error('Error:', xhr.statusText);
                });

                xhr.send(file);
            } else {
                alert('Failed to generate signed URL.');
            }
        })
        .catch(error => console.error('Error:', error));
    }
});

document.addEventListener('DOMContentLoaded', function () {
    const mediaContainers = document.querySelectorAll('.media-container');

    mediaContainers.forEach(container => {
        const url = container.getAttribute('data-url');
        const fileExtension = url.split('.').pop().toLowerCase();

        let mediaElement;

        if (['mp4', 'mov'].includes(fileExtension)) {
            // Create video element
            mediaElement = document.createElement('video');
            mediaElement.src = url;
            mediaElement.controls = true;
            mediaElement.style.width = '100%';
            mediaElement.style.height = 'auto';
            mediaElement.classList.add('rounded');
            mediaElement.classList.add('mt-2');
            mediaElement.innerText = 'Your browser does not support the video tag.';
        } else if (['jpg', 'png', 'svg', 'heic'].includes(fileExtension)) {
            // Create image element
            mediaElement = document.createElement('img');
            mediaElement.src = url;
            mediaElement.alt = 'Thumbnail';
            mediaElement.style.width = '100%';
            mediaElement.style.height = 'auto';
            mediaElement.classList.add('rounded');
            mediaElement.classList.add('mt-2');
        } else {
            // If the file type is not supported, you can handle it accordingly
            mediaElement = document.createElement('div');
            mediaElement.innerText = 'Unsupported media type';
        }

        container.appendChild(mediaElement);
    });
});