'use strict';

const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const imageUpload = document.getElementById('imageUpload');
const fontSizeInput = document.getElementById('fontSize');
const fontWeightInput = document.getElementById('fontWeight');
const customFontInput = document.getElementById('customFont');
const textAlignInput = document.getElementById('textAlign');
const lineHeightInput = document.getElementById('lineHeight');
const charSpacingInput = document.getElementById('charSpacing');
const anchorPointInput = document.getElementById('anchorPoint');
const textColorInput = document.getElementById('textColor');

let imageBox = null;
let logoBox = null;
let img = new Image();
let textBoxes = [];
let selectedTextBox = null;

imageUpload.addEventListener('change', (e) => {
    const file = e.target.files[0];
    const reader = new FileReader();
    reader.onload = (event) => {
        img.src = event.target.result;
        img.onload = () => {
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            drawTextBoxes();
        };
    };
    reader.readAsDataURL(file);
});

const resizeHandleSize = 10;
let isDragging = false;
let isDraggingImg = false
let isDraggingLogo = false
let offsetX, offsetY;
let isResizing = false;
let selectedImageBox = null;
let selectedLogoBox = null;
let isResizingImg = false;
let isResizingLogo = false;
let imageOffsetX, imageOffsetY;
let logoOffsetX, logoOffsetY;

canvas.addEventListener('mousedown', (e) => {
    const x = e.offsetX;
    const y = e.offsetY;
    for (let textBox of textBoxes) {
        if (x >= textBox.x && x <= textBox.x + textBox.width &&
            y >= textBox.y && y <= textBox.y + textBox.height) {
            selectedTextBox = textBox;
            
            // Check for resize handle
            if (x >= textBox.x + textBox.width - resizeHandleSize && 
                y >= textBox.y + textBox.height - resizeHandleSize) {
                isResizing = true;
            } else {
                isDragging = true;
                offsetX = x - textBox.x;
                offsetY = y - textBox.y;
            }
            break;
        }
    }

    if (imageBox) {
        if (x >= imageBox.x && x <= imageBox.x + imageBox.width &&
            y >= imageBox.y && y <= imageBox.y + imageBox.height) {
            if (imageBox && 
                x >= imageBox.x + imageBox.width - resizeHandleSize && 
                y >= imageBox.y + imageBox.height - resizeHandleSize) {
                isResizingImg = true;
            }
            else {
                isDraggingImg = true;
                imageOffsetX = x - imageBox.x;
                imageOffsetY = y - imageBox.y;
            }
        }
    }

    if (logoBox) {
        if (x >= logoBox.x && x <= logoBox.x + logoBox.width &&
            y >= logoBox.y && y <= logoBox.y + logoBox.height) {
            if (logoBox && 
                x >= logoBox.x + logoBox.width - resizeHandleSize && 
                y >= logoBox.y + logoBox.height - resizeHandleSize) {
                isResizingLogo = true;
            }
            else {
                isDraggingLogo = true;
                logoOffsetX = x - logoBox.x;
                logoOffsetY = y - logoBox.y;
            }
        }
    }
});

canvas.addEventListener('mousemove', (e) => {
    if (selectedTextBox && isDragging) {
        const x = e.offsetX;
        const y = e.offsetY;
        selectedTextBox.x = x - offsetX;
        selectedTextBox.y = y - offsetY;
        redrawCanvas();
    } else if (selectedTextBox && isResizing) {
        const x = e.offsetX;
        const y = e.offsetY;
        selectedTextBox.width = x - selectedTextBox.x;
        selectedTextBox.height = y - selectedTextBox.y;
        redrawCanvas();
    }
    if (isResizingImg) {
        const x = e.offsetX;
        const y = e.offsetY;
        imageBox.width = x - imageBox.x;
        imageBox.height = y - imageBox.y;
        redrawCanvas();
    }
    if (isDraggingImg) {
        const x = e.offsetX;
        const y = e.offsetY;
        imageBox.x = x - imageOffsetX;
        imageBox.y = y - imageOffsetY;
        redrawCanvas();
    }
    if (isResizingLogo) {
        const aspectRatio = logoBox.originalLogoWidth / logoBox.originalLogoHeight;
        const newWidth = e.offsetX - logoBox.x;
        const newHeight = newWidth / aspectRatio;
        logoBox.width = newWidth;
        logoBox.height = newHeight;
    
        redrawCanvas();
    }
    
    if (isDraggingLogo) {
        const x = e.offsetX;
        const y = e.offsetY;
        logoBox.x = x - logoOffsetX;
        logoBox.y = y - logoOffsetY;
        redrawCanvas();
    }
});

canvas.addEventListener('mouseup', () => {
    isDragging = false;
    isResizing = false;
    isResizingImg = false;
    isDraggingImg = false;
    isResizingLogo = false;
    isDraggingLogo = false;

});

function redrawCanvas() {
    // Fill the canvas with grey color
    ctx.fillStyle = '#c4c4c4';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Draw the uploaded image if available
    if (img && img.src) {
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    }

    if (imageBox) {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
        ctx.fillRect(imageBox.x, imageBox.y, imageBox.width, imageBox.height);
        if (selectedImageBox === imageBox) {
            ctx.fillStyle = 'black';
            ctx.fillRect(imageBox.x + imageBox.width - resizeHandleSize,
                        imageBox.y + imageBox.height - resizeHandleSize,
                        resizeHandleSize, resizeHandleSize);
        }
    }

    if (logoBox) {
        ctx.fillStyle = 'rgba(0, 255, 0, 0.5)';
        ctx.fillRect(logoBox.x, logoBox.y, logoBox.width, logoBox.height);
        if (selectedLogoBox === logoBox) {
            ctx.fillStyle = 'black';
            ctx.fillRect(logoBox.x + logoBox.width - resizeHandleSize,
                        logoBox.y + logoBox.height - resizeHandleSize,
                        resizeHandleSize, resizeHandleSize);
        }
    }

    // Draw text boxes
    drawTextBoxes();
}

function drawTextBoxes() {

    for (let textBox of textBoxes) {
        ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.fillRect(textBox.x, textBox.y, textBox.width, textBox.height);
        switch (textBox.textColor) {
            case 'black':
                ctx.fillStyle = 'black';
                break;
            case 'white':
                ctx.fillStyle = 'white';
                break;
            case 'ai':
                ctx.fillStyle = 'red';
                break;
            case 'secondary':
                ctx.fillStyle = 'blue';
                break;
        }

        ctx.font = `${textBox.fontWeight} ${textBox.fontSize}px ${textBox.fontFamily}`;

        const charSpacing = parseFloat(charSpacingInput.value);
        const adjustedLineHeight = parseFloat(textBox.fontSize) * parseFloat(textBox.lineHeight);
    
        let words = textBox.text.split(' ');
        let line = '';
        let lines = [];
        
        for (let n = 0; n < words.length; n++) {
            let testLine = line + words[n] + ' ';
            let metrics = ctx.measureText(testLine);
            let testWidth = metrics.width;
            if (testWidth > textBox.width && n > 0) {
                lines.push(line);
                line = words[n] + ' ';
            } else {
                line = testLine;
            }
        }
        lines.push(line);

        for (let i = 0; i < lines.length; i++) {
            if ((i + 1) * adjustedLineHeight <= textBox.height) {
                let lineMetrics = ctx.measureText(lines[i]);
                let lineX = textBox.x + 5; 
                
                if (textBox.textAlign === "center") {
                    lineX = textBox.x + (textBox.width / 2) - (lineMetrics.width / 2);
                } else if (textBox.textAlign === "right") {
                    lineX = textBox.x + textBox.width - lineMetrics.width - 5;
                }
                ctx.fillText(lines[i], lineX, textBox.y + (i + 1) * adjustedLineHeight);
            }
        }

        switch (textBox.anchorPoint) {
            case 'top-left':
                ctx.fillStyle = 'red';
                ctx.beginPath();
                ctx.arc(textBox.x, textBox.y, 5, 0, 2 * Math.PI);
                ctx.fill();
                break;
            case 'center':
                ctx.fillStyle = 'blue';
                ctx.beginPath();
                ctx.arc(textBox.x + textBox.width / 2, textBox.y + textBox.height / 2, 5, 0, 2 * Math.PI); 
                ctx.fill();
                break;
            case 'top-right':
                ctx.fillStyle = 'green';
                ctx.beginPath();
                ctx.arc(textBox.x + textBox.width, textBox.y, 5, 0, 2 * Math.PI); 
                ctx.fill();
                break;
        }

        if (selectedTextBox === textBox) {
            ctx.fillStyle = 'black';
            ctx.fillRect(textBox.x + textBox.width - resizeHandleSize,
                        textBox.y + textBox.height - resizeHandleSize,
                        resizeHandleSize, resizeHandleSize);
        }
    }
}

const createTextBoxButton = document.getElementById('createTextBox');
const deleteTextBoxButton = document.getElementById('deleteTextBox');
const modifyTextInput = document.getElementById('modifyText');
const applyTextButton = document.getElementById('applyText');
const createImgButton = document.getElementById('createImg');
const deleteImgButton = document.getElementById('deleteImg');
const createLogoButton = document.getElementById('createLogo');
const deleteLogoButton = document.getElementById('deleteLogo');

createTextBoxButton.addEventListener('click', () => {
    const maxCharCount = document.getElementById('maxCharCount').value;
    const promptSelectionElement = document.getElementById('promptSelection');
    const promptSelectionValue = promptSelectionElement.options[promptSelectionElement.selectedIndex].value;

    const newTextBox = {
        x: 50,
        y: 50,
        width: 250,
        height: 100,
        text: "-2E S6 :0; 2E S6 :1; 2E S6 :2; 2E S6 :E; 23 S6 :4; 2E S6 :5; 2E S6 :6; 2E S6 :7; 2E S6 :8; 2E S6 :9; 2 S6 :10; 2 S6 :11; 2 S6 :12; 2 S6 :13; 2 S6 :14; 2 S6 :15;",
        fontSize: fontSizeInput.value || '60',  
        fontWeight: fontWeightInput.value || 'normal',
        fontFamily: customFontInput.value || 'BergenText',
        textAlign: textAlignInput.value || 'left',
        lineHeight: lineHeightInput.value || '1.2',
        charSpacing: charSpacingInput.value || '0',
        anchorPoint: anchorPointInput.value || 'top-left',
        maxCharCount: maxCharCount || 40,
        prompt: promptSelectionValue || "Headline",
        textColor: textColorInput || "ai"
    };
    textBoxes.push(newTextBox);
    redrawCanvas();
});

deleteTextBoxButton.addEventListener('click', () => {
    if (selectedTextBox) {
        const index = textBoxes.indexOf(selectedTextBox);
        if (index !== -1) {
            textBoxes.splice(index, 1);
            selectedTextBox = null;
            redrawCanvas();
        }
    }
});

createImgButton.addEventListener('click', () => {
    const newImageBox = {
        x: 50,
        y: 50,
        width: 300,
        height: 200,
    };
    
    imageBox = newImageBox;
    redrawCanvas(); 
});

deleteImgButton.addEventListener('click', () => {
    imageBox = null;
    redrawCanvas(); 
});

createLogoButton.addEventListener('click', () => {
    const newLogoBox = {
        x: 400,
        y: 400,
        width: 200,
        height: 200,
        originalLogoWidth: 200,
        originalLogoHeight: 200,
    };
    
    logoBox = newLogoBox;
    redrawCanvas(); 
});

deleteLogoButton.addEventListener('click', () => {
    logoBox = null;
    redrawCanvas(); 
});

applyTextButton.addEventListener('click', () => {
    if (selectedTextBox) {
        selectedTextBox.text = modifyTextInput.value || " ";
        redrawCanvas();
    }
});

fontSizeInput.addEventListener('change', () => {
    if (selectedTextBox) {
        selectedTextBox.fontSize = fontSizeInput.value;
        redrawCanvas();
    }
});

fontWeightInput.addEventListener('change', () => {
    if (selectedTextBox) {
        selectedTextBox.fontWeight = fontWeightInput.value;
        redrawCanvas();
    }
});

customFontInput.addEventListener('change', () => {
    if (selectedTextBox) {
        selectedTextBox.fontFamily = customFontInput.value;
        redrawCanvas();
    }
});

lineHeightInput.addEventListener('change', () => {
    if (selectedTextBox) {
        selectedTextBox.lineHeight = lineHeightInput.value;
        redrawCanvas();
    }
});

charSpacingInput.addEventListener('change', () => {
    if (selectedTextBox) {
        selectedTextBox.charSpacing = charSpacingInput.value;
        redrawCanvas();
    }
});

textAlignInput.addEventListener('change', () => {
    if (selectedTextBox) {
        selectedTextBox.textAlign = textAlignInput.value;
        console.log('Updated selectedTextBox:', selectedTextBox);
        redrawCanvas();
    }
});

anchorPointInput.addEventListener('change', () => {
    if (selectedTextBox) {
        selectedTextBox.anchorPoint = anchorPointInput.value;
        console.log('Updated selectedTextBox:', selectedTextBox);
        redrawCanvas();
    }
});

textColorInput.addEventListener('change', () => {
    if (selectedTextBox) {
        selectedTextBox.textColor = textColorInput.value;
        console.log('Updated selectedTextBox:', selectedTextBox);
        redrawCanvas();
    }
});

function generateJSON() {
    const output = {};
    const isImage = document.getElementById('isImage').checked;
    const isLogo = document.getElementById('isLogo').checked;
    const isBlur = document.getElementById('isBlur').checked;
    const blurAmount = document.getElementById('blurAmount').value;

    output["isImage"] = isImage;

    if (imageBox) {
        output[`img_start_x`] = imageBox.x;
        output[`img_start_y`] = imageBox.y;
        output[`img_width`] = imageBox.width;
        output[`img_height`] = imageBox.height;
      } else {
        output[`img_start_x`] = 0;
        output[`img_start_y`] = 0;
        output[`img_width`] = 1024;
        output[`img_height`] = 1024;
      }

    output["isLogo"] = isLogo;

    if (logoBox) {
        output[`logo_start_x`] = logoBox.x;
        output[`logo_start_y`] = logoBox.y;
        output[`logo_width`] = logoBox.width;
        output[`logo_height`] = logoBox.height;
      } else {
        output[`logo_start_x`] = 0;
        output[`logo_start_y`] = 0;
        output[`logo_width`] = 0;
        output[`logo_height`] = 0;
      }

    output["isBlur"] = isBlur;
    output["blur_amount"] = blurAmount;

    textBoxes.forEach((textBox, index) => {
        const prefix = `text_box_${index + 1}`;
        let extension = textBox.fontFamily === "BergenText" ? ".otf" : ".ttf";
        let anchorX, anchorY;
        switch (textBox.anchorPoint) {
            case 'top-left':
                anchorX = textBox.x;
                anchorY = textBox.y;
                break;
            case 'center':
                anchorX = textBox.x + textBox.width / 2;
                anchorY = textBox.y + textBox.height / 2;
                break;
            case 'top-right':
                anchorX = textBox.x + textBox.width;
                anchorY = textBox.y;
                break;
        }
        
        output[`${prefix}_start_x`] = anchorX;
        output[`${prefix}_start_y`] = anchorY;
        output[`${prefix}_width`] = textBox.width;
        output[`${prefix}_height`] = textBox.height;
        output[`${prefix}_font_size`] = parseFloat(textBox.fontSize);
        output[`${prefix}_font`] = textBox.fontFamily + "-" + String(textBox.fontWeight) + extension;
        output[`${prefix}_alignment`] = textBox.textAlign;
        output[`${prefix}_anchor_point`] = textBox.anchorPoint;
        output[`${prefix}_max_char_count`] = textBox.maxCharCount;
        output[`${prefix}_prompt`] = textBox.prompt;
        output[`${prefix}_line_height`] = textBox.lineHeight;
        output[`${prefix}_text_color`] = textBox.textColor;
        
    });

    return output;
}


function downloadJSON() {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(generateJSON()));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", "settings.json");
    document.body.appendChild(downloadAnchorNode); // Required for Firefox
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
}
