
const adCostInput = document.getElementById("ad_cost");
const totalSpendOutput = document.getElementById("slider-value");
const estimatedImpressionsOutput = document.getElementById("estimated-impressions");
const estimatedLeadsOutput = document.getElementById("estimated-leads");

adCostInput.addEventListener("input", function() {
    const inputValue = parseInt(adCostInput.value);
    const estimatedImpressions = Math.round(inputValue * 13.4);
    const totalSpend = Math.round(inputValue);
    const estimatedLeads = Math.round(inputValue / 16);
    totalSpendOutput.textContent = `$${totalSpend}`;
    estimatedImpressionsOutput.textContent = `${estimatedImpressions}`;
    estimatedLeadsOutput.textContent = `${estimatedLeads}`;
});

function showSpinner() {
    var loadingOverlay = document.getElementById('loading-overlay');
    var submitButton = document.querySelector('#myForm button[type="submit"]');

    loadingOverlay.style.display = 'flex';
    submitButton.disabled = true;
}

function resizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = (textarea.scrollHeight) + 'px';
}

document.addEventListener('DOMContentLoaded', function() {
    const textareas = document.querySelectorAll('.auto-resize-textarea');
    textareas.forEach(function(textarea) {
        resizeTextarea(textarea);
        textarea.addEventListener('input', function() {
            resizeTextarea(this);
        });
    });
});