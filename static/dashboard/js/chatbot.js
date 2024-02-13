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
        // Create a new renderer
        const renderer = new marked.Renderer();
    
        // Override the image renderer method
        renderer.image = function(href, title, text) {
            // Use the original image renderer but add a class to the img element
            let imageHtml = marked.Renderer.prototype.image.call(this, href, title, text);
            // Add your class by manipulating the HTML string
            imageHtml = imageHtml.replace('<img', '<img class="chatbot-img"');
            return imageHtml;
        };
    
        // Set the options, including the custom renderer
        marked.setOptions({
            renderer: renderer
        });
    
        // Convert the markdown to HTML using the customized renderer
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
                            removeAnalyzingLoader();
                            removeLoadingMessage();
                            appendMessage(data.botMessage, botAvatar);
                            pollCount = 0;
                        } else if (data.status === 'requires_action') {
                            removeLoadingMessage();
                            console.log(data)
                            appendMessage('', botAvatar, false, true);
                            if (data.function_name === 'get_ai_post' || data.function_name === 'get_stock_post') {
                                updateContentFromAjax(data.url, data.caption)
                            } else if (data.function_name === 'get_ai_image' || data.function_name === 'get_stock_image') {
                                updateContentFromAjax(data.url, null)
                            } else if (data.function_name === 'get_caption' || data.function_name === 'get_text_post') {
                                updateContentFromAjax(null, data.caption)
                            }
                            pollCount++;
                            setTimeout(pollForResponse, pollingInterval);
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

    function appendMessage(text, avatarSrc, isLoading = false, isAnalyzing = false) {
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
    
        // messageList.appendChild(listItem);
        simpleBarContent.appendChild(listItem);
    }    
    
    function removeLoadingMessage() {
        let loadingMessages = messageList.getElementsByClassName('loader');
        while (loadingMessages.length > 0) {
            loadingMessages[0].parentNode.parentNode.parentNode.remove();
        }
    }

    function removeAnalyzingLoader() {
        let analyzingLoader = messageList.getElementsByClassName('analyzing-loader');
        while (analyzingLoader.length > 0) {
            analyzingLoader[0].parentNode.parentNode.parentNode.remove();
        }
    }

    function updateContentFromAjax(url, caption) {
        const dynamicContent = document.getElementById('dynamicContent');
        let imageElement = document.getElementById('dynamicImage');
        
        // Clear previous dynamic contents (if any)
        dynamicContent.innerHTML = '';

        // If the image element does not exist, create it
        if (!imageElement && url) {
            imageElement = document.createElement('img');
            imageElement.id = 'dynamicImage';
            imageElement.style.width = '55%'; 
            imageElement.alt = "Dynamic Image";
            imageElement.className = 'dynamic-img';
        }

        // Set the image source
        if (url) {
            imageElement.src = url;
            
            // Append the image and additional elements like breaks
            dynamicContent.appendChild(imageElement);
            dynamicContent.appendChild(document.createElement('br'));
            dynamicContent.appendChild(document.createElement('br'));
        }
    
        if (caption) {
            // Add the caption as a contenteditable div instead of an input element
            const captionWrapper = document.createElement('div');
            captionWrapper.className = 'text-box-wrapper';
            const captionElement = document.createElement('div');
            captionElement.id = 'prompt';
            captionElement.contentEditable = false;
            captionElement.className = 'text-box';
            captionElement.textContent = caption; // Set the caption text
            captionWrapper.appendChild(captionElement);
            dynamicContent.appendChild(captionWrapper);
            dynamicContent.appendChild(document.createElement('br'));
        }
    
        // Create and add the "Post to Feed" button
        // const postButton = document.createElement('button');
        // postButton.setAttribute('type', 'button');
        // postButton.className = 'btn btn-gold rounded-pill w-md waves-effect waves-light mb-3';
        // postButton.innerHTML = '<i class="mdi mdi-grid"></i> Post to Feed!';
        // postButton.onclick = function() { showSpinner(); };
        // dynamicContent.appendChild(postButton);
    }
    
});
