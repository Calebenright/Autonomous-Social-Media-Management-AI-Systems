

function decodeHtmlEntities(str) {
    return new DOMParser().parseFromString(str, 'text/html').documentElement.textContent;
}

let previouslySelected = null;
let currentPage = 1;
const imagesPerPage = 16; // Number of images per page

function selectElement(element, value, deselectPrevious = true) {
    document.getElementById(`selected_img_url`).value = value;

    if (deselectPrevious && previouslySelected) {
        previouslySelected.classList.remove('selected');
    }

    if (element) {
        element.classList.add('selected');
        previouslySelected = element;
    }
}

function createImageElement(url) {
    let imgElement = document.createElement('img');
    imgElement.src = url;
    imgElement.alt = "Thumbnail";
    imgElement.classList.add('thumbnail');
    imgElement.addEventListener('click', () => selectElement(imgElement, url));
    return imgElement;
}

function initThumbnailSelection(type, dataString=null) {
    let container = document.querySelector('.thumbnails');
    if (!container) return;

    while (container.children.length > 1) {
        container.removeChild(container.lastChild);
    }

    document.getElementById('selected_post_type').value = type;

    if (dataString) {
        let data = decodeHtmlEntities(dataString);
        let parsedData = JSON.parse(data);
        const startIndex = (currentPage - 1) * imagesPerPage;
        const endIndex = startIndex + imagesPerPage;
        const pageImages = parsedData.slice(startIndex, endIndex);

        pageImages.forEach(url => {
            let imgElement = createImageElement(url);
            container.appendChild(imgElement);
        });

        updatePaginationControls(type, parsedData.length, dataString);
    }
}

function updatePaginationControls(type, totalImages, dataString) {
    const container = document.getElementById(`pagination-controls`);
    container.innerHTML = '';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';

    const buttonContainer = document.createElement('div');
    buttonContainer.style.display = 'flex';
    buttonContainer.style.justifyContent = 'space-between';
    buttonContainer.style.marginBottom = '10px';

    const totalPages = Math.ceil(totalImages / imagesPerPage);

    if (currentPage > 1) {
        let prevButton = document.createElement(`prev-button`);
        prevButton.textContent = 'Previous';
        prevButton.className = 'pagination-button prev-button';
        prevButton.addEventListener('click', function() {
            currentPage--;
            initThumbnailSelection(type, dataString);
        });
        buttonContainer.appendChild(prevButton);
    }

    if (currentPage < totalPages) {
        let nextButton = document.createElement(`next-button`);
        nextButton.textContent = 'Next';
        nextButton.className = 'pagination-button next-button';
        nextButton.addEventListener('click', function() {
            currentPage++;
            initThumbnailSelection(type, dataString);
        });
        buttonContainer.appendChild(nextButton);
    }

    container.appendChild(buttonContainer);
    let pageInfo = document.createElement('span');
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
    pageInfo.className = 'page-info';
    container.appendChild(pageInfo);
}


function selectNone() {
    selectElement(null, "None", true);
    let noneThumbnail = document.querySelector(`.none-thumbnail`);
    noneThumbnail.classList.add('selected');
    previouslySelected = noneThumbnail;
}

function setFormValueAndShowSpinner(formType, formId) {
    var updatedCaption = document.getElementById('prompt').innerText;
    document.getElementById('editedCaption').value = updatedCaption;
    document.getElementById('formAction').value = formType;
    showSpinner();
    document.getElementById(formId).submit();
}

function setElaineValueAndShowSpinner(formType, formId) {
    var updatedCaption = document.getElementById('prompt').innerText;
    document.getElementById('editedCaption').value = updatedCaption;
    document.getElementById('formAction').value = formType;
    document.getElementById('elaineNum').value = document.getElementById('selectize-select').value;
    showSpinner();
    document.getElementById(formId).submit();
}

function toggleSocialMedia(media) {
    var element = document.getElementById(media);
    var isVisible = element.style.display != "none";
    document.getElementById(media + '_visible').value = isVisible ? "false" : "true";
    element.style.display = isVisible ? "none" : "inline";
}

function resetSocialMedia() {
    ['facebook', 'instagram', 'linkedin', 'google_business'].forEach(media => {
        var element = document.getElementById(media);
        if (element) {
            element.style.display = "inline";
            document.getElementById(media + '_visible').value = "true";
        }
    });
}
