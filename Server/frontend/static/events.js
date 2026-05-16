const eventContainer = document.querySelector('#eventContainer');

function cleanEvents()
{
    eventContainer.replaceChildren();
}

function pushEvent(data)
{
    var template = document.querySelector("#EventCard");

    // Оборачиваем фрагмент в div, чтобы querySelector и onclick работали корректно
    var wrapper = document.createElement('div');
    wrapper.appendChild(template.content.cloneNode(true));

    wrapper.querySelector('#name').textContent = data['eventName'];
    wrapper.querySelector('#image').src = data['eventImage']['url'];
    wrapper.querySelector('#place').textContent = data['eventPlace'];

    var timeLabel = data['eventStartDate'] + " | ";
    if (data['isAllDay'] == true)
        timeLabel += "Весь день";
    else
        timeLabel += data['eventStartTime'] + "-" + data['eventEndTime'];
    wrapper.querySelector('#time').textContent = timeLabel;

    // Добавляем в DOM, потом вешаем обработчик
    eventContainer.appendChild(wrapper);

    var detailsBtn = wrapper.querySelector('#detailsButton');
    detailsBtn.addEventListener('click', () => askAboutEvent(data));
}

function askAboutEvent(data)
{
    var eventName = data['eventName'] || 'это мероприятие';
    var question = 'Расскажи подробнее о мероприятии «' + eventName + '»';

    pushMessage('user', question);

    var chatPanel = document.querySelector('#chatPanel');
    if (chatPanel) chatPanel.scrollTop = chatPanel.scrollHeight;

    setChatLoading(true);
    checkSendAvailability();

    sendChatMessage(question, (responce, err) => {
        setChatLoading(false);
        checkSendAvailability();

        if (!responce || responce.text == null || responce.text == '')
            return;

        pushMessage('ai', responce.text);

        if (chatPanel) chatPanel.scrollTop = chatPanel.scrollHeight;
    });
}

getEvents((data) =>
{
    data.forEach(element => {
        pushEvent(element);
    });
});
