const swapQueueMembers = (queueId, leftPosition, rightPosition) => {
    if (leftPosition === null || rightPosition === null) {
        alert("Вы должны выбрать ровно одного пользователя из каждого из двух списков.");
        return;
    }

    if (leftPosition === rightPosition) {
        alert("Выбранные пользователи должны отличаться.");
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

const swapQueueMembersDesktop = queueId => {
    const leftPositionInputOrNull = document.querySelector("input[name='left-member']:checked");
    const rightPositionInputOrNull = document.querySelector("input[name='right-member']:checked");

    const leftPosition = leftPositionInputOrNull !== null ? parseInt(leftPositionInputOrNull.value) : null;
    const rightPosition = rightPositionInputOrNull !== null ? parseInt(rightPositionInputOrNull.value) : null;
    swapQueueMembers(queueId, leftPosition, rightPosition);
};

const swapQueueMembersMobile = queueId => {
    const leftPositionSelectOrNull = document.querySelector("select[name='left-member']").value;
    const rightPositionSelectOrNull = document.querySelector("select[name='right-member']").value;

    const leftPosition = leftPositionSelectOrNull !== "" ? parseInt(leftPositionSelectOrNull) : null;
    const rightPosition = rightPositionSelectOrNull !== "" ? parseInt(rightPositionSelectOrNull) : null;
    swapQueueMembers(queueId, leftPosition, rightPosition);
};