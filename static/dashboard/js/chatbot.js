
document.addEventListener('DOMContentLoaded', function () {
    var viewport = document.querySelector("meta[name=viewport]");
    if (screen.width <= 768) { // Assumes 768px is your cutoff for mobile devices
        if (!viewport) {
            viewport = document.createElement('meta');
            viewport.name = 'viewport';
            document.getElementsByTagName('head')[0].appendChild(viewport);
        }
        viewport.content = "width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no";
    }
});

document.addEventListener('DOMContentLoaded', () => {

    // ======================
    // Variables Declaration
    // ======================

    const avatars = {
        elaine: elaineAvatar,
        jerry: jerryAvatar,
    };
    let activeCharacter = 'elaine';
    let activeAvatar = avatars[activeCharacter];
    const chatTitle = document.getElementById('agentTitle');
    const sendButton = document.querySelector('.chat-send');
    const messageInput = document.querySelector('.conversation-input input');
    const messageList = document.querySelector('.conversation-list');
    const simpleBarContent = messageList.querySelector('.simplebar-content');
    const csrfToken = getCookie('csrftoken');
    const isSubscriber = userSettings.isSubscriber === true;
    const pollingInterval = 2000;
    const maxPollAttempts = 25;
    let pollCount = 0;

    // ================
    // Helper Functions
    // ================
    
    /**
     * Switches the active chat character.
     */
    function switchChatCharacter(character) {
        activeCharacter = character;
        activeAvatar = avatars[character];
        uppercaseName = character.charAt(0).toUpperCase() + character.slice(1);
        chatTitle.textContent = `${uppercaseName}`;
        clearChat(`Hey boss! It's ${uppercaseName}. How can I help you today?`, activeAvatar);
        updateCharacterColor(character);
    }

    function updateCharacterColor(character) {
        const rootStyle = document.documentElement.style;
        switch(character) {
            case 'elaine':
                rootStyle.setProperty('--active-character-bg', 'var(--elaine-bg-color)');
                break;
            case 'jerry':
                rootStyle.setProperty('--active-character-bg', 'var(--jerry-bg-color)');
                break;
            default:
                rootStyle.setProperty('--active-character-bg', 'var(--default-bg-color)');
        }
    }

    /**
     * Sends the user's message.
     */
    function sendMessage() {
        const message = messageInput.value.trim();
        if (message) {
            messageInput.value = ''; 
            appendMessage(message, userLogo);
            appendMessage('', activeAvatar, true);
            sendChat(message);
        }
    }

    /**
     * Clears the chat.
     */
    function clearChat(message, avatar, shouldConfirm = false) {
        const clearChatAction = () => {
            $.ajax({
                url: '/clear_chat/',
                type: 'POST',
                headers: { 'X-CSRFToken': csrfToken },
                success: () => {
                    simpleBarContent.innerHTML = '';
                    appendMessage(message, avatar);
                },
                error: (error) => console.error('Error:', error),
            });
        };

        if (!shouldConfirm || confirm('Are you sure you want to clear the chat?')) {
            clearChatAction();
        }
    }

    /**
     * Gets a cookie value by name.
     */
    function getCookie(name) {
        const cookieValue = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`));
        return cookieValue ? cookieValue[2] : '';
    }

    /**
     * Convert to Markdown.
     */
    function convertMarkdownToHtml(markdownText) {
        const renderer = new marked.Renderer();
    
        renderer.image = function(href, title, text) {
            let imageHtml = marked.Renderer.prototype.image.call(this, href, title, text);
            imageHtml = imageHtml.replace('<img', '<img class="chatbot-img"');
            return imageHtml;
        };
    
        marked.setOptions({
            renderer: renderer
        });
    
        return marked.parse(markdownText);
    }

    function removeAnalyzingLoader() {
        let analyzingLoader = messageList.getElementsByClassName('analyzing-loader');
        while (analyzingLoader.length > 0) {
            analyzingLoader[0].parentNode.parentNode.parentNode.remove();
        }
    }
    
    function removeLoadingMessage() {
        let loadingMessages = messageList.getElementsByClassName('loader');
        while (loadingMessages.length > 0) {
            loadingMessages[0].parentNode.parentNode.parentNode.remove();
        }
    }

    function displayErrorMessage(errorMsg) {
        var errorMessagesContainer = document.getElementById('error-messages-container');
        if (errorMessagesContainer.querySelectorAll('.messages').length === 0) {
            var messagesUl = document.createElement('ul');
            messagesUl.className = 'messages';
            errorMessagesContainer.appendChild(messagesUl);
        }
        var errorMessageLi = document.createElement('li');
        errorMessageLi.className = 'danger';
        errorMessageLi.setAttribute('data-message-id', 'ajaxError');
        var textNode = document.createTextNode(errorMsg); // Create text node with error message
        errorMessageLi.appendChild(textNode); // Append the text node to the li element
        var closeButton = document.createElement('span');
        closeButton.className = 'closebtn';
        closeButton.innerHTML = '&times;';
        closeButton.onclick = function() { this.parentElement.style.display = 'none'; }; // Corrected to hide the parent li element
        errorMessageLi.appendChild(closeButton);
        errorMessagesContainer.querySelector('.messages').appendChild(errorMessageLi);
    }

    // ===============
    // Event Listeners
    // ===============

    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            sendMessage();
        }
    });

    document.getElementById('clearChat').addEventListener('click', () => {
        clearChat(`Hey boss! It's ${uppercaseName}. How can I help you today?`, activeAvatar, true);
    });

    // ==================
    // Character Switching
    // ==================

    const hitboxes = document.querySelectorAll('.character-hitbox');
    hitboxes.forEach((hitbox, index) => {
        hitbox.addEventListener('click', toggleDisplay);
        hitbox.addEventListener('mouseenter', () => addGlow(index));
        hitbox.addEventListener('mouseleave', () => removeGlow(index));
    });

    function toggleDisplay(event) {
        if (userSettings.isSubscriber || event.currentTarget.getAttribute('data-avatar-name') === 'elaine'){
            hideAllToggleCards();
            const toggleCardId = event.currentTarget.getAttribute('data-toggle-card-id');
            const avatarName = event.currentTarget.getAttribute('data-avatar-name');
            const toggleCard = document.getElementById(toggleCardId);
            toggleCard.style.display = "block";
            switchChatCharacter(avatarName);
        } else {
            displayErrorMessage('Please subscribe to use this feature');
        }
        
    }

    function hideAllToggleCards() {
        document.querySelectorAll('.toggleCard').forEach(card => {
            card.style.display = 'none';
        });
    }

    function addGlow(index) {
        document.querySelectorAll('.character')[index]?.classList.add('glow');
    }

    function removeGlow(index) {
        document.querySelectorAll('.character')[index]?.classList.remove('glow');
    }

    // ===================
    // Initial Chat Restore
    // ===================

    function restoreChatHistory() {
        if (storedChatMessages && storedChatMessages.length > 0) {
            storedChatMessages.forEach(({ content, role }) => {
                appendMessage(content, role === 'bot' ? activeAvatar : userLogo);
            });
        }
    }

    restoreChatHistory();

    // =====================
    // Message Sending & Polling
    // =====================

    function sendChat(message) {
        $.ajax({
            url: '/start_chat/', 
            type: 'post',
            headers: {
                'X-CSRFToken': csrfToken 
            },
            dataType: 'json',
            data: {
                'message': message,
                'character': activeCharacter
            },
            success: function (data) {
                if (data.status === 'pending') {
                    pollForResponse();
                } else if (data.status === 'error') {
                    appendMessage(data.botMessage, activeAvatar);
                }
            },
            error: function(data) {
                removeLoadingMessage();
                var $errorMessagesContainer = $('#error-messages-container');
                if ($errorMessagesContainer.find('.messages').length === 0) {
                    $errorMessagesContainer.append('<ul class="messages"></ul>');
                }
                var errorText = data.responseJSON.error || "An error occured.";
                var errorMessage = '<li class="danger" data-message-id="ajaxError">' + errorText +
                    '<span class="closebtn" onclick="closeMessage(this);">&times;</span></li>';
                $errorMessagesContainer.find('.messages').append(errorMessage);
            }
        });
    }

    function pollForResponse() {
        if (pollCount < maxPollAttempts) {
            $.ajax({
                url: '/get_chat/',
                type: 'get',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                dataType: 'json',
                success: function(data) {
                    if (pollCount < maxPollAttempts) {
                        if (data.status === 'completed') {
                            console.log(data.url);
                            if (data.url) {
                                appendMessage(`![Generated Image](${data.url})`, activeAvatar, false, false, true);
                            }
                            removeAnalyzingLoader();
                            removeLoadingMessage();
                            appendMessage(data.botMessage, activeAvatar);
                            pollCount = 0;
                        } else if (data.status === 'requires_action') {
                            removeLoadingMessage();
                            appendMessage('', activeAvatar, false, true);
                            pollCount++;
                            setTimeout(pollForResponse, pollingInterval);
                        } else {
                            pollCount++;
                            setTimeout(pollForResponse, pollingInterval);
                        }
                    } else {
                        removeAnalyzingLoader();
                        removeLoadingMessage();
                        console.log('Error: Max poll attempts reached.');
                        appendMessage('There was an error getting your request. Please refresh and try again or contact us!', activeAvatar);
                        pollCount = 0;
                    }
                    
                },
                error: function(error) {
                    removeAnalyzingLoader();
                    removeLoadingMessage();
                    console.log('Error:', error);
                    appendMessage('There was an error getting your request. Please refresh and try again or contact us!', activeAvatar);
                    pollCount = 0;
                }
            });
        } else {
            removeAnalyzingLoader();
            removeLoadingMessage();
            console.log('Error: Max poll attempts reached.');
            appendMessage('There was an error getting your request. Please refresh and try again or contact us!', activeAvatar);
            pollCount = 0;
        }
    }

    function appendMessage(text, avatarSrc, isLoading = false, isAnalyzing = false, isUrl = false) {
        let listItem = document.createElement('li');
        listItem.className = avatarSrc === userLogo ? 'odd' : '';
        if (avatarSrc !== userLogo) {
            text = convertMarkdownToHtml(text);
        }
        if (isLoading) {
            listItem.innerHTML = 
                '<div class="message-list">' +
                    '<div class="chat-avatar">' +
                        '<img src="' + avatarSrc + '" alt="">' +
                    '</div>' +
                    '<div class="conversation-text">' +
                        '<div class="ctext-wrap">' +
                            '<div class="loader">' +
                                '<div class="loader-dot"></div>' +
                                '<div class="loader-dot"></div>' +
                                '<div class="loader-dot"></div>' +
                            '</div>' +
                        '</div>' +
                    '</div>' +
                '</div>';
        } else if (isAnalyzing) {
            listItem.innerHTML =
                '<div class="message-list">' +
                    '<div class="chat-avatar">' +
                        '<img src="' + avatarSrc + '" alt="">' +
                    '</div>' +
                    '<div class="conversation-text">' +
                        '<div class="ctext-wrap">' +
                            '<div class="analyzing-loader">' +
                                '<svg class="circular-loader" viewBox="25 25 50 50">' +
                                    '<circle class="path" cx="50" cy="50" r="20" fill="none" stroke-width="2" stroke-miterlimit="10"/>' +
                                '</svg>' +
                                '<p>Analyzing...</p>' +
                            '</div>' +
                        '</div>' +
                    '</div>' +
                '</div>';
        } else {
            listItem.innerHTML = 
                '<div class="message-list">' +
                    '<div class="chat-avatar">' +
                        '<img src="' + avatarSrc + '" alt="">' +
                    '</div>' +
                    '<div class="conversation-text">' +
                        '<div class="ctext-wrap">' +
                            '<p>' + text + '</p>' +
                        '</div>' +
                    '</div>' +
                '</div>';
        }
    
        simpleBarContent.appendChild(listItem);
        scrollToBottom();
        console.log(simpleBarContent);
    }    

    function scrollToBottom() {
        simpleBarContent.scrollTop = simpleBarContent.scrollHeight;
    }

    // =======================================
    // Initial Character Highlighting (if needed)
    // =======================================

    if (hitboxes.length > 0) {
        hitboxes[0].click();
    }
});
