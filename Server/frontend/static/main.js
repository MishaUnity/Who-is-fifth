const chatContainer = document.querySelector('#chatContainer');
const sendButton = document.querySelector('#sendButton');
const messageInput = document.querySelector('#messageInput');

function pushMessage(source, text)
{
    var template = document.querySelector("#OtherMessageCard");
    if (source == "user")
        template = document.querySelector("#UserMessageCard");

    var element = template.content.cloneNode(true);
    var textElement = element.querySelector('#text');

    textElement.textContent = text;

    chatContainer.appendChild(element);
}

function checkSendAvailability()
{
    if (messageInput.value == "")
    {
        sendButton.disabled = true;
        return false;
    }

    sendButton.disabled = false;
    return true;
}

messageInput.oninput = () =>
{
    checkSendAvailability();
}

sendButton.onclick = () =>
{
    var inputText = messageInput.value;
    messageInput.value = "";
    
    pushMessage("user", inputText);
    checkSendAvailability();
}

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
    };
}

getEvents();