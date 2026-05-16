const chatContainer = document.querySelector('#chatContainer');
const sendButton = document.querySelector('#sendButton');
const messageInput = document.querySelector('#messageInput');
const chatLoading = document.querySelector('#chatLoading');
const deleteChatButton = document.querySelector('#deleteChatButton');

const accountLabel = document.querySelector('#accountLabel');

var awaitingResponce = false;

function setChatLoading(state)
{
    awaitingResponce = state;
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

function cleanMessages()
{
    chatContainer.replaceChildren();
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

deleteChatButton.onclick = () =>
{
    deleteChatHistory(() => 
    {
        cleanMessages();
    });
}

function sendMessage()
{
    var inputText = messageInput.value;
    messageInput.value = "";

    pushMessage("user", inputText);

    setChatLoading(true);
    checkSendAvailability();

    sendChatMessage(inputText, (responce, err) => {
        setChatLoading(false);
        checkSendAvailability();

        if (responce.text == null || responce.text == "")
            return;
        
        pushMessage("ai", responce.text);
    });
}

SESSION_ID = getOrCreateSessionId()

getChatHistory((data) => 
{
    data.history.forEach(element => {
        console.log(element);
        pushMessage(element['role'], element['content']);
    });
});


if (SESSION_ID.startsWith("session_"))
{
    accountLabel.textContent = "Гость | " + SESSION_ID
    loginButton.textContent = "Войти"
}
else
{
    accountLabel.textContent = SESSION_ID
    loginButton.textContent = "Выйти"
}

loginButton.onclick = () =>
{
    localStorage.removeItem("session_id");
    window.location.replace("/login");
}