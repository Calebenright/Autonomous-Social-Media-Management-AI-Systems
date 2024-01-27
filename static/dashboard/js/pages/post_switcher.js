

function decodeHtmlEntities(str) {
    return new DOMParser().parseFromString(str, 'text/html').documentElement.textContent;
}

let previouslySelected = { ad: null, graphic: null, photo: null };

function selectElement(type, element, value, deselectPrevious = true) {
    document.getElementById(`selected_${type}_url`).value = value;

    if (deselectPrevious && previouslySelected[type]) {
        previouslySelected[type].classList.remove('selected');
    }

    if (element) {
        element.classList.add('selected');
        previouslySelected[type] = element;
    }
}

function initThumbnailSelection(type, dataString=null, containerClass=null) {
    let container = document.querySelector(containerClass);
    if (container) {
        while (container.firstChild) {
            container.removeChild(container.firstChild);
        }
        
        let specialDiv = document.createElement('div');
        specialDiv.classList.add('thumbnail', 'none-thumbnail', `${type}-none`);
        specialDiv.setAttribute('onclick', `selectNone('${type}', '${type}-none')`);    
    
        let aiSpan = document.createElement('span');
        aiSpan.classList.add('ai-text');
        aiSpan.textContent = 'AI';
    
        specialDiv.appendChild(aiSpan);
        container.prepend(specialDiv);
    }

    document.getElementById('selected_post_type').value = type;

    if (dataString) {
        let data = decodeHtmlEntities(dataString);
        JSON.parse(data).forEach(url => {
            let imgElement = document.createElement('img');
            imgElement.src = url;
            imgElement.alt = "Thumbnail";
            imgElement.classList.add('thumbnail');
            imgElement.addEventListener('click', () => selectElement(type, imgElement, url));
            container.appendChild(imgElement);
        });
    }
}

function selectNone(type, aiElementId) {
    selectElement(type, null, "None", true);
    let noneThumbnail = document.querySelector(`.${type}-none`);
    noneThumbnail.classList.add('selected');
    previouslySelected[type] = noneThumbnail;
    document.getElementById(aiElementId).style.display = "block";
}

function setFormValueAndShowSpinner(formType, formId) {
    var updatedCaption = document.getElementById('prompt').innerText;
    document.getElementById('editedCaption').value = updatedCaption;
    document.getElementById('formAction').value = formType;
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



// function decodeHtmlEntities(str) {
//     const parser = new DOMParser();
//     return parser.parseFromString(str, 'text/html').documentElement.textContent;
// }


// let imageStockURLsString = decodeHtmlEntities("{{ user_settings.image_tags }}");
// if (imageStockURLsString){
//     let imageStockURLs = JSON.parse(imageStockURLsString);
//     let thumbnailsStockDiv = document.querySelector('.stock-thumbnails');
//     imageStockURLs.forEach(url => {
//         let imgStockElement = document.createElement('img');
//         imgStockElement.src = url;
//         imgStockElement.alt = "Thumbnail";
//         imgStockElement.classList.add('thumbnail');
//         imgStockElement.addEventListener('click', () => selectStockImage(imgStockElement, url));
//         thumbnailsStockDiv.appendChild(imgStockElement);
//     });
// } else {
//     let imageStockURLs = '';
// }
// let previouslySelectedStockImage = null;
// const aiStockImage = document.getElementById('ai-stock-image')

// function selectStockImage(imgStockElement, url) {
//     document.getElementById('selected_stock_image_url').value = url;

//     if (previouslySelectedStockImage) {
//         previouslySelectedStockImage.classList.remove('selected');
//     }
//     imgStockElement.classList.add('selected');
//     previouslySelectedStockImage = imgStockElement;
//     aiStockImage.style.display = "none";
// }

// function selectNoneStock() {
//     document.getElementById('selected_stock_image_url').value = "None";
    
//     if (previouslySelectedStockImage) {
//         previouslySelectedStockImage.classList.remove('selected');
//     }
//     let noneStockThumbnail = document.querySelector('.none-thumbnail');
//     noneStockThumbnail.classList.add('selected');
//     previouslySelectedStockImage = noneStockThumbnail;
//     aiStockImage.style.display = "block";
    
// }

// let imageURLsString = decodeHtmlEntities("{{ user_settings.image_tags }}");
// if (imageURLsString){
//     let imageURLs = JSON.parse(imageURLsString);
//     let thumbnailsDiv = document.querySelector('.graphic-thumbnails');
//     imageURLs.forEach(url => {
//         let imgElement = document.createElement('img');
//         imgElement.src = url;
//         imgElement.alt = "Thumbnail";
//         imgElement.classList.add('thumbnail');
//         imgElement.addEventListener('click', () => selectImage(imgElement, url));
//         thumbnailsDiv.appendChild(imgElement);
//     });
// } else {
//     let imageURLs = '';
// }

// let previouslySelectedImage = null;
// const aiImage = document.getElementById('ai-image')

// function selectImage(imgElement, url) {
//     document.getElementById('selected_image_url').value = url;

//     if (previouslySelectedImage) {
//         previouslySelectedImage.classList.remove('selected');
//     }
//     imgElement.classList.add('selected');
//     previouslySelectedImage = imgElement;
//     aiImage.style.display = "none";
// }

// function selectNone() {
//     document.getElementById('selected_image_url').value = "None";
    
//     if (previouslySelectedImage) {
//         previouslySelectedImage.classList.remove('selected');
//     }
//     let noneThumbnail = document.querySelector('.none-thumbnail');
//     noneThumbnail.classList.add('selected');
//     previouslySelectedImage = noneThumbnail;
//     aiImage.style.display = "block";
    
// }

// let adCreativeImageURLsString = decodeHtmlEntities("{{ user_settings.image_tags }}");

// if (adCreativeImageURLsString){
//     let adCreativeImageURLs = JSON.parse(adCreativeImageURLsString);
//     let adCreativeThumbnailsDiv = document.querySelector('.ad-creative-thumbnails');
//     adCreativeImageURLs.forEach(url => {
//         let imgAdElement = document.createElement('img');
//         imgAdElement.src = url;
//         imgAdElement.alt = "Thumbnail";
//         imgAdElement.classList.add('thumbnail');
//         imgAdElement.addEventListener('click', () => selectAdImage(imgAdElement, url));
//         adCreativeThumbnailsDiv.appendChild(imgAdElement);
//     });
// } else {
//     let adCreativeImageURLs = '';
// }

// const aiAdImage = document.getElementById('ai-ad-image')
// let previouslySelectedAdCreativeImage = null;

// function selectAdImage(imgAdElement, url) {
//     document.getElementById('selected_ad_creative_image_url').value = url;

//     if (previouslySelectedAdCreativeImage) {
//         previouslySelectedAdCreativeImage.classList.remove('selected');
//     }
//     imgAdElement.classList.add('selected');
//     previouslySelectedAdCreativeImage = imgAdElement;
//     aiAdImage.style.display = "none";
// }

// function selectNoneAd() {
//     document.getElementById('selected_ad_creative_image_url').value = "None";
    
//     if (previouslySelectedAdCreativeImage) {
//         previouslySelectedAdCreativeImage.classList.remove('selected');
//     }
//     let noneAdThumbnail = document.querySelector('.none-ad-thumbnail');
//     noneAdThumbnail.classList.add('selected');
//     previouslySelectedAdCreativeImage = noneAdThumbnail;
//     aiAdImage.style.display = "block";
// }

// function setFormValueAndShowSpinner(formType, formId) {
//     var updatedCaption = document.getElementById('prompt').innerText;
//     document.getElementById('editedCaption').value = updatedCaption;
//     document.getElementById('formAction').value = formType;
//     showSpinner();
//     document.getElementById(formId).submit();
// }

// function toggleSocialMedia(media) {
//     var element = document.getElementById(media);
//     var isVisible = element.style.display != "none";
//     document.getElementById(media + '_visible').value = isVisible ? "false" : "true";
//     element.style.display = isVisible ? "none" : "inline";
// }

// function resetSocialMedia() {
//     ['facebook', 'instagram', 'linkedin', 'google_business'].forEach(media => {
//         var element = document.getElementById(media);
//         if (element) {
//             element.style.display = "inline";
//             document.getElementById(media + '_visible').value = "true";
//     }
//     });
// }