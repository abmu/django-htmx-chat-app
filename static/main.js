let currentAreFriends;
let isNewMessagesText;
let authenticationFailed = false;

document.body.addEventListener('htmx:wsClose', (event) => {
    authenticationFailed = true;
});

function attemptReconnection() {
    console.log('test')
    if (authenticationFailed) {
        authenticationFailed = false;
        var socketElt = document.body; // Assuming the ws-connect is on the body
        ensureWebSocket(socketElt);
    }
}
  
htmx.attemptWebSocketReconnection = attemptReconnection;

document.body.addEventListener('htmx:afterSwap', () => {
    htmx.attemptWebSocketReconnection();
});

const jsonMessageHandlers = {
    'recent_chat_html': (jsonData) => updateRecentChats(jsonData.html),
    'message_html': (jsonData) => updateMessages(jsonData.html),
    'decrement_unread_count': (jsonData) => decrementUnreadCount(jsonData.otherUserUuid, jsonData.count),
    'update_recent_chat_read_status': (jsonData) => updateRecentChatReadStatus(jsonData.otherUserUuid),
    'update_message_read_status': (jsonData) => updateMessageReadStatus(jsonData.messageUuid),
    'update_all_messages_read_status': (jsonData) => updateAllMessagesReadStatus(jsonData.senderUuid),
    'update_section_count': (jsonData) => updateSectionCount(jsonData.page, jsonData.section, jsonData.action),
    'remove_user_from_section': (jsonData) => removeUserFromSection(jsonData.section, jsonData.otherUserUuid),
    'add_user_html_to_section': (jsonData) => addUserHtmlToSection(jsonData.section, jsonData.html),
    'update_friendship': (jsonData) => updateFriendship(jsonData.areFriends),
    'account_deleted': (jsonData) => handleAccountDeleted()
};

function handleJsonMessage(jsonData) {
    if (jsonMessageHandlers[jsonData.type] !== undefined) {
        jsonMessageHandlers[jsonData.type](jsonData);
    }
}

document.body.addEventListener('htmx:wsBeforeMessage', (event) => {
    const wsMessage = event.detail.message;
    const jsonData = JSON.parse(wsMessage);
    handleJsonMessage(jsonData);
    event.preventDefault(); // Cancel event to prevent any further unnecessary processing by HTMX
});

const dateFormatter = new Intl.DateTimeFormat(undefined, {
    dateStyle: 'short'
});

const timeFormatter = new Intl.DateTimeFormat(undefined, {
    timeStyle: 'short'
});

function getLocalTimestamp(utcTimestampString) {
    return new Date(utcTimestampString);
}

function getDate(timestamp) {
    return dateFormatter.format(timestamp);
}

function getTime(timestamp) {
    return timeFormatter.format(timestamp);
}

function insertLocalTimestamp(element) {
    const utcTimestamp = element.dataset.utcTimestamp;
    const localTimestamp = getLocalTimestamp(utcTimestamp);
    const time = getTime(localTimestamp);
    const date = getDate(localTimestamp);
    element.dataset.time = time;
    element.dataset.date = date;

    const timeElement = element.querySelector('.time');
    if (timeElement) {
        timeElement.textContent = time;
    }

    const dateElement = element.querySelector('.date');
    if (dateElement) {
        dateElement.textContent = date;
    }
}

function htmlToElement(html, trim = true) {
    html = trim ? html.trim() : html;
    if (!html) return null;

    const template = document.createElement('template');
    template.innerHTML = html;
    const result = template.content.children;

    if (result.length === 1) return result[0];
    return result;
}

function setUnreadCount(recentChatElement, newUnreadCount) {
    recentChatElement.dataset.unreadCount = newUnreadCount
    recentChatElement.querySelector('.unread-count').textContent = newUnreadCount;
}

function updateRecentChats(newRecentChatHtml) {
    const newRecentChatElement = htmlToElement(newRecentChatHtml);
    insertLocalTimestamp(newRecentChatElement);

    const oldRecentChatElement = document.getElementById(newRecentChatElement.id);
    if (oldRecentChatElement) {
        oldRecentChatElement.remove();
    }

    let unreadCount = newRecentChatElement.dataset.unreadCount;
    if (unreadCount === 'increment') {
        unreadCount = oldRecentChatElement ? parseInt(oldRecentChatElement.dataset.unreadCount) + 1 : 1;
        setUnreadCount(newRecentChatElement, unreadCount);
    }

    document.getElementById('recent-chats').insertAdjacentElement('afterbegin', newRecentChatElement);
}

function updateElementReadStatus(element) {
    const readStatusElement = element.querySelector('.read-status');
    readStatusElement.textContent = 'True';
}

function updateRecentChatReadStatus(otherUserUuid) {
    const recentChatElement = document.getElementById(`chat-${otherUserUuid}`);
    updateElementReadStatus(recentChatElement);
}

function decrementUnreadCount(otherUserUuid, count) {
    const recentChatElement = document.getElementById(`chat-${otherUserUuid}`);
    const oldUnreadCount = parseInt(recentChatElement.dataset.unreadCount);
    const newUnreadCount = Math.max(0, oldUnreadCount - count);
    setUnreadCount(recentChatElement, newUnreadCount);
}

function updateSectionCount(page, section, action) {
    const suffix = page === 'home' ? '-home' : '';
    const sectionElement = document.getElementById(`${section}-count${suffix}`);
    const oldCount = parseInt(sectionElement.textContent);
    const newCount = action === 'increment' ? oldCount + 1 : Math.max(0, oldCount - 1);
    sectionElement.textContent = newCount;
}

document.body.addEventListener('htmx:wsConfigSend', (event) => {
    const elementId = event.detail.elt.id;
    if (elementId === 'load') {
        return;
    }
    // Cancel event and don't send message if the users don't have a mutual friendship, or if the message is blank
    const content = event.detail.parameters.content;
    if (!currentAreFriends || !content.trim()) {
        event.preventDefault();
    }
});

document.body.addEventListener('htmx:wsAfterSend', (event) => {
    const elementId = event.detail.elt.id;
    if (elementId === 'load') {
        return;
    }
    const chatInputELement = document.getElementById('chat-input');
    chatInputELement.value = '';
});

function isNewUnreadMessage(messageElement, userUuid) {
    return messageElement.dataset.recipientUuid === userUuid && messageElement.dataset.read === 'False';
}

function clearNewMessagesText() {
    const newMessagesTextElement = document.getElementById('new-messages');
    newMessagesTextElement.remove();
}

function updateMessages(newMessageHtml) {
    const newMessageElement = htmlToElement(newMessageHtml);
    insertLocalTimestamp(newMessageElement);

    const messagesContainer = document.getElementById('messages');

    const date = newMessageElement.dataset.date;
    const dateTextElement = document.getElementById(`date-${date}`);
    if (dateTextElement === null) {
        const dateTextHtml = getDateTextHtml(date);
        messagesContainer.insertAdjacentHTML('beforeend', dateTextHtml);
    }

    messagesContainer.insertAdjacentElement('beforeend', newMessageElement);

    if (isNewMessagesText) {
        isNewMessagesText = false;
        clearNewMessagesText();
    }
}

function updateMessageElementReadStatus(messageElement) {
    messageElement.dataset.read = 'True';
    updateElementReadStatus(messageElement);
}

function updateMessageReadStatus(messageUuid) {
    const messageElement = document.getElementById(`message-${messageUuid}`);
    if (messageElement && messageElement.dataset.read === 'False') {
        updateMessageElementReadStatus(messageElement);
    }
}

function updateAllMessagesReadStatus(senderUuid) {
    const messageElements = document.querySelectorAll(`.message[data-sender-uuid='${senderUuid}'][data-read='False']`);
    messageElements.forEach(updateMessageElementReadStatus);
}

function updateFriendship(areFriends) {
    currentAreFriends = areFriends;
    const friendshipStatusElement = document.getElementById('friendship-status');
    friendshipStatusElement.innerHTML = currentAreFriends ? '' : getNotFriendsTextHtml();
}

function removeUserFromSection(section, otherUserUuid) {
    const prefix = section === 'friends' ? 'friend-' : `${section}-`
    const userElement = document.getElementById(`${prefix}${otherUserUuid}`);
    userElement.remove();
}

function binaryInsertInOrder(newElement, container) {
    const children = container.children;
    const newUsername = newElement.dataset.username;

    let left = 0;
    let right = children.length - 1;

    while (left <= right) {
        const mid = Math.floor((left + right) / 2);
        const midUsername = children[mid].dataset.username.toLowerCase();

        if (midUsername < newUsername) {
            left = mid + 1;
        } else if (newUsername < midUsername) {
            right = mid - 1;
        } else {
            return;
        }
    }

    if (left < children.length) {
        container.insertBefore(newElement, children[left]);
    } else {
        container.appendChild(newElement);
    }
}

function addUserHtmlToSection(section, html) {
    const newUserElement = htmlToElement(html);
    const suffix = section === 'friends' ? '-list' : '-requests';
    const container = document.getElementById(`${section}${suffix}`);
    binaryInsertInOrder(newUserElement, container);
}

function handleAccountDeleted() {
    window.location.replace(`/`);
}