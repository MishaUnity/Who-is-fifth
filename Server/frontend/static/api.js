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

function getEvents()
{
    var headers = { 'Content-Type': 'application/json' };

    console.log("Я работаю!");

    try {
        const responce = await fetch('/api/events/get', {
            method: 'GET',
            headers: headers
        });
    } catch (err) {
        console.error(err);
    } finally {
        console.log(responce);
    }
}