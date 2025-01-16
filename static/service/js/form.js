
// Initialize Dropify
if ($('[data-plugins="dropify"]').length > 0) {
    $('[data-plugins="dropify"]').dropify({
        messages: {
            default: "File Upload",
            replace: "Replace File",
            remove: "Remove",
            error: "Ooops, something wrong happened."
        },
        error: {
            fileSize: "The file size is too big (300mb max)."
        }
    });
}

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

function closeMessage(element) {
    element.parentElement.style.display = 'none'; // Hide the message
    const messageId = element.parentElement.getAttribute('data-message-id');
    
    // Store the closed message ID in local storage
    const closedMessages = JSON.parse(localStorage.getItem('closed_messages')) || [];
    closedMessages.push(messageId);
    localStorage.setItem('closed_messages', JSON.stringify(closedMessages));
  }

const input = document.getElementById('files');
const folder_value = document.getElementById('folder_name')
if (folder_value) {
    folder_name = folder_value.value;
}
const thumbnailsContainer = document.getElementById('thumbnails-container');
const uploadOverlay = document.getElementById('upload-overlay');
const progressBar = document.getElementById('upload-progress-bar');
const submitButton = document.getElementById('submit-button');

if (input) {
    input.addEventListener('change', function () {
        submitButton.disabled = true;
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
                img.classList.add('mb-1');
                previewDiv.appendChild(img);
            } else if (file.type.startsWith('video/')) {
                const video = document.createElement('video');
                video.src = URL.createObjectURL(file);
                video.style.width = '100%';
                video.style.height = 'auto';
                video.classList.add('rounded');
                video.classList.add('mt-2');
                video.classList.add('mb-1');
                video.controls = true;
                previewDiv.appendChild(video);
            }
            thumbnailsContainer.appendChild(previewDiv);

            const formData = new FormData();
            formData.append('file_name', file.name);
            formData.append('folder_name', folder_name);
            formData.append('csrfmiddlewaretoken', '{{ csrf_token }}');
            
            const fileName = document.getElementById('file_name');
            if (fileName) {
                fileName.value = file.name;
            }

            fetch(sendForm, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.url) {
                    var fileName = data.file_name;
                    uploadOverlay.style.display = 'block';
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
                        uploadOverlay.style.display = 'none';
                        if (xhr.status === 200) {
                            fetch(makePublic, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': getCookie('csrftoken')
                                },
                                body: JSON.stringify({ folder_name, file_name: fileName })
                            })
                            .then(response => response.json())
                            .then(data => {
                                submitButton.disabled = false;
                            })
                            .catch(error => {
                                console.error('Error making file public:', error);
                                submitButton.disabled = false;
                                alert('Failed to make the file public');
                            });
                        } else {
                            submitButton.disabled = false;
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
}

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
            mediaElement.classList.add('mb-1');
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
            mediaElement.classList.add('mb-1');
        } else {
            // If the file type is not supported, you can handle it accordingly
            mediaElement = document.createElement('div');
            mediaElement.innerText = 'Unsupported media type';
        }

        container.appendChild(mediaElement);
    });
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}