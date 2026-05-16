const usernameInput = document.querySelector('#usernameInput');
const passwordInput = document.querySelector('#passwordInput');
const registerButton = document.querySelector('#registerButton');
const loginButton = document.querySelector('#loginButton');
const errorText = document.querySelector('#errorText');

registerButton.onclick = (event) =>
{
    if (usernameInput.value.length < 8 && passwordInput.value.length < 8)
    {
        ShowError("Имя и пароль должны иметь хотя бы 8 символов")
        return;
    }

    var username = usernameInput.value;
    var password = passwordInput.value;

    register(username, password, (responce) => {
        ApplyToken(responce['token']);
    });
}

loginButton.onclick = (event) =>
{
    if (usernameInput.value.length < 8 && passwordInput.value.length < 8)
    {
        ShowError("Имя и пароль должны иметь хотя бы 8 символов")
        return;
    }

    var username = usernameInput.value;
    var password = passwordInput.value;

    login(username, password, (responce) => {
        ApplyToken(responce['token']);
    });
}

function ApplyToken(token)
{
    if (token == null || token == "")
    {
        ShowError("Ошибка, вы правильно указали имя и пароль?")
        return;
    }

    localStorage.setItem("session_id", token);
    SESSION_ID = token;

    window.location.href = "/"; 
}

function ShowError(text)
{
    errorText.style.display = text == null ? "none" : "flex";
    errorText.textContent = text
}