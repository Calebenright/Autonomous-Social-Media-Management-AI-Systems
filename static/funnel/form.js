

// INSTAGRAM //

function closeMessage(element) {
element.parentElement.style.display = 'none';
const messageId = element.parentElement.getAttribute('data-message-id');

const closedMessages = JSON.parse(localStorage.getItem('closed_messages')) || [];
closedMessages.push(messageId);
localStorage.setItem('closed_messages', JSON.stringify(closedMessages));
}