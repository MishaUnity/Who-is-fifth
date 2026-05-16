// function sendMessage()
// {
//     // Оно не работает, не трогайте
//     var headers = { 'Content-Type': 'application/json' };
//     if (token) headers['Authorization'] = 'Bearer ' + token;

//     try {
//         const responce = await fetch('/api/chat', {
//         method: 'POST',
//         headers: headers,
//         body: JSON.stringify({
//             message: text,
//             session_id: sessionId,
//             history: history.slice(-10)
//         })
//     });

//     const data = await resp.json();

//     if (!resp.ok) 
//     {
//         appendMessage('assistant', 'Ошибка: ' + (data.detail || data.error || 'Неизвестная ошибка'));
//         return;
//     }

//     appendMessage('assistant', data.content);
//     history.push({ role: 'assistant', content: data.content });
//     saveHistory(history);

//     } catch (err) {
//         appendMessage('assistant', 'Не удалось отправить сообщение. Проверьте соединение.');
//         console.error(err);
//     } finally {
//         showLoading(false);
//         setInputEnabled(true);
//         input.focus();
//     }
// }

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

// Получение событий
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