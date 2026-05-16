const chatContainer = document.querySelector('#chatContainer');
const sendButton = document.querySelector('#sendButton');
const messageInput = document.querySelector('#messageInput');
const chatLoading = document.querySelector('#chatLoading');

var awaitingResponce = false;

function setChatLoading(state)
{
    chatLoading.style.display = state ? "flex" : "none";
}

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
    if (messageInput.value == "" || awaitingResponce)
    {
        sendButton.disabled = true;
        return false;
    }

    sendButton.disabled = false;
    return true;
}

messageInput.oninput = (event) =>
{
    checkSendAvailability();
}

messageInput.onkeydown = (event) => 
{
    if (event.key === 'Enter' && !event.shiftKey) 
    {
        event.preventDefault();
        sendMessage();
    }
}

sendButton.onclick = () =>
{
    sendMessage();
}

function sendMessage()
{
    var inputText = messageInput.value;
    messageInput.value = "";

    pushMessage("user", inputText);

    awaitingResponce = true;
    checkSendAvailability();

    sendChatMessage(inputText, (responce, err) => {
        awaitingResponce = false;
        checkSendAvailability();

        console.log(err, responce);

        if (responce.text == null || responce.text == "")
            return;
        
        pushMessage("ai", responce.text);
    });
}