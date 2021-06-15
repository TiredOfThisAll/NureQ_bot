const swapQueueMembers = queueId => {
    const leftPositionInputOrNull = document.querySelector("input[name='left-member']:checked");
    const rightPositionInputOrNull = document.querySelector("input[name='right-member']:checked");
    if (leftPositionInputOrNull === null || rightPositionInputOrNull === null) {
        alert("Вы должны выбрать ровно одного пользователя из каждого из двух списков.");
        return;
    }

    const leftPosition = parseInt(leftPositionInputOrNull.value);
    const rightPosition = parseInt(rightPositionInputOrNull.value);

    if (leftPosition === rightPosition) {
        alert("Выбранные пользователи должны отличатся.");
        return;
    }

    setSpinnerVisibility(true);
    const body = JSON.stringify({
        left_position: leftPosition,
        right_position: rightPosition,
    });
    fetch(`/api/queues/${queueId}/swap-queue-members`, {method: "PUT", body})
        .then(response => {
            if (response.status !== 204) {
                response.text().then(alert);
                return Promise.reject();
            }
            location.href = `/queues/${queueId}`;
        })
        .finally(() => {
            setSpinnerVisibility(false);
        });
};