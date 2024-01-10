"use strict";

!function(i) {
    function e() {
        this.$body = i("body")
    }
    e.prototype.init = function() {
        Dropzone.autoDiscover = false;
        i('[data-plugin="dropzone"]').each(function() {
            var e = i(this).attr("action"),
                o = i(this).data("previewsContainer"),
                e = {
                    url: e
                };
            o && (e.previewsContainer = o);
            var o = i(this).data("uploadPreviewTemplate");
            o && (e.previewTemplate = i(o).html());
            i(this).dropzone(e)
        })
    };
    i.FileUpload = new e();
    i.FileUpload.Constructor = e;
}(window.jQuery);

window.jQuery.FileUpload.init();

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

const tagInput = document.getElementById('tagInput');
const tagBubbles = document.getElementById('tagBubbles');
const tags = tagsArray;

tagInput.addEventListener('keydown', function(event) {
if (event.key === 'Enter' || event.key === ',') {
event.preventDefault();
const tagValue = tagInput.value.trim();
if (tagValue) {
addTag(tagValue);
tagInput.value = '';
}
}
});

function addTag(tagValue) {
tags.push(tagValue);
const tagBubble = document.createElement('div');
tagBubble.classList.add('tag-bubble');
tagBubble.textContent = tagValue;
tagBubbles.appendChild(tagBubble);
tagBubble.addEventListener('click', function() {
removeTag(tagValue);
});
}

function removeTag(tagValue) {
const index = tags.indexOf(tagValue);
if (index !== -1) {
tags.splice(index, 1);
updateTagBubbles();
}
}

function updateTagBubbles() {
tagBubbles.innerHTML = '';
tags.forEach(tagValue => {
const tagBubble = document.createElement('div');
tagBubble.classList.add('tag-bubble');
tagBubble.textContent = tagValue;
tagBubbles.appendChild(tagBubble);
tagBubble.addEventListener('click', function() {
removeTag(tagValue);
});
});
}

function updateHiddenInput() {
const tagsInput = document.querySelector('input[name="tags"]');
tagsInput.value = tags.join(',');
}

const tagForm = document.getElementById('tagForm');
tagForm.addEventListener('submit', function(event) {
updateHiddenInput();
tagForm.submit();
});

updateTagBubbles();
