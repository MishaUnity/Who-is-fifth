<<<<<<< HEAD
=======
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

>>>>>>> 695edabebc936b61e8ebc2cb7a7f635a491019fa
function getOrCreateSessionId() {
    let sid = localStorage.getItem("session_id")
    if (!sid) {
        sid = "session_" + Math.random().toString(36).slice(2)
        localStorage.setItem("session_id", sid)
    }
    return sid
}

const SESSION_ID = getOrCreateSessionId()

function getToken() {
    return localStorage.getItem("auth_token")
}

// Отправка сообщения в чат
function sendChatMessage(text, callback) {
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + getToken()
        },
        body: JSON.stringify({
            message: text,
            session_id: SESSION_ID,
            history: []
        })
    })
    .then(response => response.json())
    .then(data => callback(data))
    .catch(error => {
        console.error('Ошибка:', error)
        callback(null)
    })
}

// Очистка чата — удаляет историю из БД и генерирует новый session_id
function clearChat(callback) {
    fetch('/api/chat/clear', {
        method: 'DELETE',
        headers: {
            'Authorization': 'Bearer ' + getToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        // Генерируем новый session_id
        localStorage.removeItem("session_id")
        location.reload()
    })
    .catch(error => console.error('Ошибка:', error))
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

login("test", "test", (responce) => {console.log(responce)});

// Регистрация
async function register(username, password, callback) 
{
    fetch('/register', {
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