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

getEvents((data) =>
{
    data.forEach(element => {
        pushEvent(element);
    });
});