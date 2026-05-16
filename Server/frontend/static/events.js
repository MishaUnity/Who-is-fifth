const eventContainer = document.querySelector('#eventContainer');

function cleanEvents()
{
    eventContainer.replaceChildren();
}

function pushEvent(data)
{
    var template = document.querySelector("#EventCard");

    var element = template.content.cloneNode(true);
    element.querySelector('#name').textContent = data['eventName'];
    element.querySelector('#image').src = data['eventImage']['url'];
    element.querySelector('#place').textContent = data['eventPlace'];

    var timeLabel = data['eventStartDate'] + " | ";
    if (data['isAllDay'] == true)
        timeLabel += "Весь день";
    else
        timeLabel += data['eventStartTime'] + "-" + data['eventEndTime'];
    element.querySelector('#time').textContent = timeLabel;

    eventContainer.appendChild(element);
}

function askAboutEvent(data)
{
    var eventName = data['eventName'] || 'это мероприятие';
    var eventPlace = data['eventPlace'] || 'сириус';
    var eventStartDate = data['eventStartDate'] || 'сириус';
    var question = 'Расскажи подробнее о мероприятии ' + eventName + ' в ' + eventPlace + ' ' + eventStartDate;

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