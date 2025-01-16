"use strict";

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
    var loadingOverlay = document.getElementById('loading-overlay');
    var submitButton = document.querySelector('#myForm button[type="submit"]');

    loadingOverlay.style.display = 'flex';
    submitButton.disabled = true;
}

// -------------------- IMAGE TAGS ------------------------ //

let currentPage = 1;
const imagesPerPage = 30;
const imageTags = imageTagsArray;
let totalImages = imageTags.length; // Should be declared with 'let' if it needs to be updated

function removeImageTag(imageUrl) {
    const index = imageTags.indexOf(imageUrl);
    if (index !== -1) {
        imageTags.splice(index, 1);
        updateTotalImagesAndThumbnails();
    }
}

function updateTotalImagesAndThumbnails() {
    totalImages = imageTags.length; // Update totalImages based on the current number of image tags
    updateImageTagThumbnails(); // Then update the thumbnails displayed
    updatePaginationControls(); // And also update the pagination controls accordingly
}

function updateImageTagThumbnails() {
    const startIndex = (currentPage - 1) * imagesPerPage;
    const endIndex = startIndex + imagesPerPage;
    const paginatedImageUrls = imageTags.slice(startIndex, endIndex); // Get images for the current page

    const imageTagThumbnails = document.getElementById("imageTagThumbnails");
    imageTagThumbnails.innerHTML = ''; // Clear existing thumbnails

    paginatedImageUrls.forEach(imageUrl => {
        const imageThumbnail = document.createElement('div');
        imageThumbnail.classList.add('image-tag-thumbnail');

        const imgElement = document.createElement('img');
        imgElement.src = imageUrl;
        imgElement.alt = "Image Tag";
        imageThumbnail.appendChild(imgElement);

        // Overlay div
        const overlay = document.createElement('div');
        overlay.classList.add('overlay');

        // Create a remove button
        const removeBtn = document.createElement('button');
        const icon = document.createElement('i');
        icon.classList.add('fe-delete');
        removeBtn.appendChild(icon);
        removeBtn.classList.add('remove-btn');
        removeBtn.onclick = function(event) {
            event.preventDefault();
            removeImageTag(imageUrl);
        };
        overlay.appendChild(removeBtn);


        // Create a download link
        const downloadLink = document.createElement('a');
        downloadLink.href = imageUrl;
        downloadLink.download = imageUrl.split('/').pop();
        const icon2 = document.createElement('i');
        icon2.classList.add('fe-download-cloud');
        downloadLink.appendChild(icon2);
        downloadLink.classList.add('download-link');
        overlay.appendChild(downloadLink);

        // Append overlay to imageThumbnail
        imageThumbnail.appendChild(overlay);

        imageTagThumbnails.appendChild(imageThumbnail);
    });

    updatePaginationControls(); // Call to update pagination controls based on current state
}

function updatePaginationControls() {
    const container = document.getElementById('pagination-controls');
    container.innerHTML = '';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';

    const buttonContainer = document.createElement('div');
    buttonContainer.style.display = 'flex';
    buttonContainer.style.justifyContent = 'space-between';
    buttonContainer.style.marginBottom = '10px';

    const totalPages = Math.ceil(totalImages / imagesPerPage);

    // Previous Button
    if (currentPage > 1) {
        const prevButton = document.createElement('button');
        prevButton.textContent = 'Previous';
        prevButton.className = 'pagination-button prev-button';
        prevButton.type = 'button';
        prevButton.onclick = function() {
            if (currentPage > 1) {
                currentPage--;
                updateImageTagThumbnails(); // Refresh thumbnails to show the previous page
            }
        };
        buttonContainer.appendChild(prevButton);
    }

    // Next Button
    if (currentPage < totalPages) {
        const nextButton = document.createElement('button');
        nextButton.textContent = 'Next';
        nextButton.className = 'pagination-button next-button';
        nextButton.type = 'button';
        nextButton.onclick = function() {
            if (currentPage < totalPages) {
                currentPage++;
                updateImageTagThumbnails(); // Refresh thumbnails to show the next page
            }
        };
        buttonContainer.appendChild(nextButton);
    }

    // Page Information Display
    container.appendChild(buttonContainer);
    const pageInfo = document.createElement('span');
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    pageInfo.className = 'page-info';
    container.appendChild(pageInfo);
}


function updateHiddenImageInput() {
    const imageTagsInput = document.querySelector('input[name="imageTags"]');
    imageTagsInput.value = imageTags.join(',');
}

const imageTagForm = document.getElementById('imageTagForm');
imageTagForm.addEventListener('submit', function(event) {
    updateHiddenImageInput();
    imageTagForm.submit();
});

function generateImageSignedUrl() {
    var photoFile = document.getElementById('imageUpload').files[0];
    var folderName = 'image_library';

    if (!photoFile) {
        sendPhotoTagForm();
    } else {
        var formData = new FormData();
        formData.append('folder_name', folderName);
        formData.append('file_name', photoFile.name);

        var xhr = new XMLHttpRequest();
        xhr.open('POST', formUrl, true);
        xhr.setRequestHeader('X-CSRFToken', csrf_token);

        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var response = JSON.parse(xhr.responseText);
                var signedUrl = response.url;
                var fileName = response.file_name;
                
                uploadPhoto(signedUrl, photoFile);
            }
        };

        xhr.send(formData);
    }
}

function uploadPhoto(signedUrl, photoFile) {
    var xhr = new XMLHttpRequest();
    xhr.open('PUT', signedUrl, true);
    xhr.setRequestHeader('Content-Type', 'application/octet-stream');

    xhr.upload.onprogress = function(e) {
        if (e.lengthComputable) {
            var percentComplete = (e.loaded / e.total) * 100;
            document.getElementById('image-upload-progress-bar').style.width = percentComplete + '%';
            document.getElementById('image-upload-progress-bar').innerText = percentComplete.toFixed(2) + '%';
        }
    };

    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                document.getElementById('image-url').value = photoFile.name;
                showSpinner();
                sendPhotoTagForm();
            } else {
                alert('Error uploading photo: ' + xhr.statusText);
            }
        }
    };

    xhr.send(photoFile);
}

function sendPhotoTagForm() {
    updateHiddenPhotoInput();
    document.getElementById('imageTagForm').submit();
}

function updateHiddenPhotoInput() {
    const photoTagsInput = document.querySelector('input[name="imageTags"]');
    photoTagsInput.value = photoTagsArray.join(',');
}

updateImageTagThumbnails();

// -------------------- VIDEO TAGS ------------------------ //

let currentvideoPage = 1;
const videosPerPage = 30;
const videoTags = videoTagsArray;
let totalvideos = videoTags.length; // Should be declared with 'let' if it needs to be updated

function removevideoTag(videoUrl) {
    const index = videoTags.indexOf(videoUrl);
    if (index !== -1) {
        videoTags.splice(index, 1);
        updateTotalvideosAndThumbnails();
    }
}

function updateTotalvideosAndThumbnails() {
    totalvideos = videoTags.length; // Update totalvideos based on the current number of video tags
    updatevideoTagThumbnails(); // Then update the thumbnails displayed
    updatePaginationControls(); // And also update the pagination controls accordingly
}

function updatevideoTagThumbnails() {
    const startvideoIndex = (currentvideoPage - 1) * videosPerPage;
    const endIndex = startvideoIndex + videosPerPage;
    const paginatedvideoUrls = videoTags.slice(startvideoIndex, endIndex); // Get videos for the current page

    const videoTagThumbnails = document.getElementById("videoTagThumbnails");
    videoTagThumbnails.innerHTML = ''; // Clear existing thumbnails

    paginatedvideoUrls.forEach(videoUrl => {
        const videoThumbnail = document.createElement('div');
        videoThumbnail.classList.add('video-tag-thumbnail');

        const videoElement = document.createElement('video');
        videoElement.src = videoUrl;
        videoElement.controls = true;
        videoElement.alt = "Video Tag";
        videoThumbnail.appendChild(videoElement);

        // Create a remove button
        const removeBtn = document.createElement('button');
        const icon3 = document.createElement('i');
        icon3.classList.add('fe-delete');
        removeBtn.appendChild(icon3);
        removeBtn.classList.add('video-tag-remove-btn');
        removeBtn.onclick = function(event) {
            event.preventDefault();
            removevideoTag(videoUrl);
        };

        // Append overlay to videoThumbnail
        videoThumbnail.appendChild(removeBtn);

        videoTagThumbnails.appendChild(videoThumbnail);
    });

    updatevideoPaginationControls(); // Call to update pagination controls based on current state
}

function updatevideoPaginationControls() {
    const container = document.getElementById('video-pagination-controls');
    container.innerHTML = '';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';

    const buttonContainer = document.createElement('div');
    buttonContainer.style.display = 'flex';
    buttonContainer.style.justifyContent = 'space-between';
    buttonContainer.style.marginBottom = '10px';

    const totalPages = Math.ceil(totalvideos / videosPerPage);

    // Previous Button
    if (currentvideoPage > 1) {
        const prevButton = document.createElement('button');
        prevButton.textContent = 'Previous';
        prevButton.className = 'pagination-button prev-button';
        prevButton.type = 'button';
        prevButton.onclick = function() {
            if (currentvideoPage > 1) {
                currentvideoPage--;
                updatevideoTagThumbnails(); 
            }
        };
        buttonContainer.appendChild(prevButton);
    }

    // Next Button
    if (currentvideoPage < totalPages) {
        const nextButton = document.createElement('button');
        nextButton.textContent = 'Next';
        nextButton.className = 'pagination-button next-button';
        nextButton.type = 'button';
        nextButton.onclick = function() {
            if (currentvideoPage < totalPages) {
                currentvideoPage++;
                updatevideoTagThumbnails(); // Refresh thumbnails to show the next page
            }
        };
        buttonContainer.appendChild(nextButton);
    }

    // Page Information Display
    container.appendChild(buttonContainer);
    const videopageInfo = document.createElement('span');
    videopageInfo.textContent = `Page ${currentvideoPage} of ${totalPages}`;
    videopageInfo.className = 'page-info';
    container.appendChild(videopageInfo);
}

function generateSignedUrl() {
    var videoFile = document.getElementById('videoUpload').files[0];
    var folderName = 'video_library';

    if (!videoFile) {
        sendVideoTagForm();
    } else {
        var formData = new FormData();
        formData.append('folder_name', folderName);
        formData.append('file_name', videoFile.name);

        var xhr = new XMLHttpRequest();
        xhr.open('POST', formUrl, true);
        xhr.setRequestHeader('X-CSRFToken', csrf_token);

        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var response = JSON.parse(xhr.responseText);
                var signedUrl = response.url;
                var fileName = response.file_name;
                
                uploadVideo(signedUrl, videoFile);
            }
        };

        xhr.send(formData);
    }
}

function uploadVideo(signedUrl, videoFile) {
    var xhr = new XMLHttpRequest();
    xhr.open('PUT', signedUrl, true);
    xhr.setRequestHeader('Content-Type', 'application/octet-stream');

    xhr.upload.onprogress = function(e) {
        if (e.lengthComputable) {
            var percentComplete = (e.loaded / e.total) * 100;
            document.getElementById('upload-progress-bar').style.width = percentComplete + '%';
            document.getElementById('upload-progress-bar').innerText = percentComplete.toFixed(2) + '%';
        }
    };

    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                document.getElementById('video-url').value = videoFile.name;
                sendVideoTagForm();
            } else {
                alert('Error uploading video: ' + xhr.statusText);
            }
        }
    };

    xhr.send(videoFile);
}

function sendVideoTagForm() {
    updateHiddenvideoInput();
    document.getElementById('videoTagForm').submit();
    showSpinner();
}

function updateHiddenvideoInput() {
    const videoTagsInput = document.querySelector('input[name="videoTags"]');
    videoTagsInput.value = videoTagsArray.join(',');
}

updatevideoTagThumbnails();
