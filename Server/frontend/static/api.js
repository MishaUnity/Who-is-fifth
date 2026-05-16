function sendChatMessage(text, callback)
{
    var headers = { 'Content-Type': 'application/json' };

    fetch('/api/chat/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                session: SESSION_ID
            })
        })
    .then(response => response.json())
    .then(data => {
        callback(data);
    })
    .catch(error => {
        callback(null);
    });
}

function getOrCreateSessionId() {
    let sid = localStorage.getItem("session_id")
    if (!sid) {
        sid = "session_" + Math.random().toString(36).slice(2)
        localStorage.setItem("session_id", sid)
    }
    return sid
}

var SESSION_ID = getOrCreateSessionId()

function getToken() {
    return localStorage.getItem("session_id")
}

// Загрузка истории чата
function getChatHistory(callback) 
{
    fetch('/api/chat/history', 
    {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({'token' : SESSION_ID})
    })
    .then(response => response.json())
    .then(data => {
        callback(data);
    })
    .catch(error => console.error('Ошибка:', error))
}

// Удаление истории
function deleteChatHistory(callback)
{
    fetch('/api/chat/delete', 
    {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({'token' : SESSION_ID})
    })
    .then(response => response.json())
    .then(data => {
        callback(data);
    })
    .catch(error => console.error('Ошибка:', error))
}

// Отправка сообщения в чат
function sendChatMessage(text, callback)
{
    var headers = { 'Content-Type': 'application/json' };

    fetch('/api/chat/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                'text': text,
                'session': SESSION_ID
            })
        })
    .then(response => response.json())
    .then(data => {
        callback(data);
    })
    .catch(error => {
        callback(null);
    });
}

// Авторизация
function login(username, password, callback) {
    fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.token) {
            localStorage.setItem('auth_token', data.token)
        }
        callback(data)
    })
    .catch(error => console.error('Ошибка:', error))
}

// Получение событий афиши
async function getEvents(callback)
{
    var headers = { 'Content-Type': 'application/json' };

    fetch('/api/events/get_afisha', {
            method: 'GET',
            headers: headers
        })
    .then(response => response.json())
    .then(data => {
        callback(data);
    })
    .catch(error => console.error('Ошибка:', error));
}

// Регистрация
async function register(username, password, callback) 
{
    fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: username,
                password: password
            })
        })
    .then(response => response.json())
    .then(data => {
        callback(data);
    })
    .catch(error => console.error('Ошибка:', error));
}

// Авторизация
async function login(username, password, callback) 
{
    fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: username,
                password: password
            })
        })
    .then(response => response.json())
    .then(data => {
        localStorage.setItem('auth_token', data.token);
        callback(data);
    })
    .catch(error => console.error('Ошибка:', error));
}