$(document).ready(function () {
    $('.dropify').dropify();

    $('#uploadForm').on('submit', function (event) {
        event.preventDefault();
        var fileInput = document.getElementById('fileInput');
        var emailInput = document.getElementById('emailInput');
        var submitButton = document.getElementById('submitButton');

        if (!fileInput.files.length || !emailInput.checkValidity()) {
            alert('Please select a file and enter a valid email');
            return;
        }

        var file = fileInput.files[0];
        var email = emailInput.value;

        submitButton.disabled = true;

        // Request a signed URL from the server
        $.ajax({
            url: '/generate_signed_url/',
            type: 'POST',
            data: {
                file_name: file.name,
                email: email
            },
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function (response) {
                var signedUrl = response.url;
                var publicUrl = response.public_url;
                var extension = response.extension;
                uploadFileToGCS(signedUrl, file, publicUrl, email, extension);
            },
            error: function (xhr, status, error) {
                alert('Error generating signed URL');
                console.error('Error generating signed URL:', error);
                submitButton.disabled = false;
            }
        });
    });

    function uploadFileToGCS(signedUrl, file, publicUrl, email, extension) {
        var progressBar = $('.progress-bar');

        $.ajax({
            url: signedUrl,
            type: 'PUT',
            data: file,
            contentType: 'application/octet-stream',
            processData: false,
            xhr: function () {
                var xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener("progress", function (evt) {
                    if (evt.lengthComputable) {
                        var percentComplete = evt.loaded / evt.total;
                        progressBar.width(percentComplete * 100 + '%');
                    }
                }, false);
                return xhr;
            },
            success: function (response) {
                alert('File uploaded successfully');
                window.location.href = '/upload/?file_url=' + encodeURIComponent(signedUrl) + '&email=' + encodeURIComponent(email) + '&extension=' + encodeURIComponent(extension);
            },
            error: function (xhr, status, error) {
                alert('Error uploading file');
                console.error('Error uploading file:', error);
                submitButton.disabled = false;
            }
        });
    }

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
