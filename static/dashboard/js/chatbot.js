document.addEventListener('DOMContentLoaded', function() {
    const sendButton = document.querySelector('.chat-send');
    const messageInput = document.querySelector('.conversation-input input');
    const messageList = document.querySelector('.conversation-list');
    const simpleBarContent = messageList.querySelector('.simplebar-content')

    const pollingInterval = 2000;
    const maxPollAttempts = 25;
    let pollCount = 0;

    function getCookie(name) {
        const cookieValue = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
        return cookieValue ? cookieValue.pop() : '';
    }
    var csrfToken = getCookie('csrftoken');

    function convertMarkdownToHtml(markdownText) {
        return marked.parse(markdownText);
    }    

    if (storedChatMessages && storedChatMessages.length > 0) {
        storedChatMessages.forEach(function(message) {
            if (message.role === 'bot') {
                appendMessage(message.content, botAvatar);
            } else {
                appendMessage(message.content, userLogo);
            }
        });
    }

    sendButton.addEventListener('click', sendMessage);

    messageInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            sendMessage();
        }
    });
    
    function sendMessage() {
        var message = messageInput.value;
        messageInput.value = ''; 

        appendMessage(message, userLogo);
        console.log(message)
        appendMessage('', botAvatar, true);
        sendChat(message)
    }

    document.getElementById('clearChat').addEventListener('click', function() {
        if (confirm('Are you sure you want to clear the chat?')) {
            $.ajax({
                url: '/clear_chat/',
                type: 'post',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                success: function(response) {
                    simpleBarContent.innerHTML = '';
                    appendMessage('How can I assist you?', botAvatar);
                    console.log('Chat cleared and session reset.');
                },
                error: function(error) {
                    console.error('Error:', error);
                }
            });
        }
    });

    function sendChat(message) {
        $.ajax({
            url: '/start_chat/', 
            type: 'post',
            headers: {
                'X-CSRFToken': csrfToken 
            },
            dataType: 'json',
            data: {
                'message': message
            },
            success: function (data) {
                if (data.status === 'pending') {
                    console.log(data);
                    pollForResponse();
                } else if (data.status === 'error') {
                    appendMessage(data.botMessage, botAvatar);
                }
            },
            error: function(xhr) {
                removeLoadingMessage();
                if (xhr.status == 400 && xhr.responseJSON && xhr.responseJSON.error) {
                    console.log('Error:', xhr.responseJSON.error);
                    var $errorMessagesContainer = $('#error-messages-container');
                    if ($errorMessagesContainer.find('.messages').length === 0) {
                        $errorMessagesContainer.append('<ul class="messages"></ul>');
                    }
                    var errorMessage = '<li class="danger" data-message-id="ajaxError">' + xhr.responseJSON.error +
                        '<span class="closebtn" onclick="closeMessage(this);">&times;</span></li>';
                    $errorMessagesContainer.find('.messages').append(errorMessage);
                }
            }
        });
    }

    function pollForResponse() {
        if (pollCount < maxPollAttempts) {
            $.ajax({
                url: '/get_chat/', // URL for polling
                type: 'get',
                headers: {
                    'X-CSRFToken': csrfToken
                },
                dataType: 'json',
                success: function(data) {
                    if (pollCount < maxPollAttempts) {
                        if (data.status === 'completed') {
                            removeLoadingMessage();
                            appendMessage(data.botMessage, botAvatar);
                            pollCount = 0; 
                        } else {
                            pollCount++;
                            setTimeout(pollForResponse, pollingInterval);
                        }
                    } else {
                        removeLoadingMessage();
                        appendMessage('There was an error getting your request. Please refresh and try again or contact us!', botAvatar);
                        pollCount = 0;
                    }
                    
                },
                error: function(error) {
                    removeLoadingMessage();
                    appendMessage('There was an error getting your request. Please refresh and try again or contact us!', botAvatar);
                    pollCount = 0;
                }
            });
        } else {
            removeLoadingMessage();
            appendMessage('There was an error getting your request. Please refresh and try again or contact us!', botAvatar);
            pollCount = 0;
        }
    }

    function appendMessage(text, avatarSrc, isLoading = false) {
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
    
        // messageList.appendChild(listItem);
        simpleBarContent.appendChild(listItem);
    }    
    
    function removeLoadingMessage() {
        let loadingMessages = messageList.getElementsByClassName('loader');
        while (loadingMessages.length > 0) {
            loadingMessages[0].parentNode.parentNode.parentNode.remove();
        }
    }
});
