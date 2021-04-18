const deleteQueue = queueId => {
    const isConfirmed = confirm(`Вы уверены, что хотите удалить очередь с ID: ${queueId}`);
    if (!isConfirmed) {
        return;
    }
    setSpinnerVisibility(true);
    fetch(`/api/queues/${queueId}`, {method: "DELETE"})
        .then(response => {
            if (response.status !== 204) {
                return Promise.reject();
            }
            location.reload();
        })
        .finally(() => {
            setSpinnerVisibility(false)
        });
};

const deleteMember = (queueId, queueName, queueMemberName, queueMemberUserId) => {
    const isConfirmed = confirm(`Вы уверены, что хотите удалить ${queueMemberName} из ${queueName} очереди`);
    if (!isConfirmed) {
        return;
    }
    setSpinnerVisibility(true);
    fetch(`/api/queues/${queueId}/members/${queueMemberUserId}`, {method: "DELETE"})
        .then(response => {
            if (response.status !== 204) {
                return Promise.reject();
            }
            location.reload();
        })
        .finally(() => {
            setSpinnerVisibility(false)
        });
};

const setMemberCrossedOut = (queueId, queueMemberUserId, newValue) => {
    setSpinnerVisibility(true);
    fetch(`/api/queues/${queueId}/members/${queueMemberUserId}/crossed`, {method: "PUT", body: newValue})
        .then(response => {
            if (response.status !== 204) {
                return Promise.reject();
            }
            location.reload();
        })
        .finally(() => {
            setSpinnerVisibility(false)
        });
};

const moveUpQueueMember = (queueId, queueMemberPosition) => {
    setSpinnerVisibility(true);
    fetch(`/api/queues/${queueId}/move-up`, {method: "PUT", body: queueMemberPosition})
        .then(response => {
            if (response.status !== 204) {
                return Promise.reject();
            }
            location.reload();
        })
        .finally(() => {
            setSpinnerVisibility(false)
        });
};

const moveDownQueueMember = (queueId, queueMemberPosition) => {
    setSpinnerVisibility(true);
    fetch(`/api/queues/${queueId}/move-down`, {method: "PUT", body: queueMemberPosition})
        .then(response => {
            if (response.status !== 204) {
                return Promise.reject();
            }
            location.reload();
        })
        .finally(() => {
            setSpinnerVisibility(false)
        });
};

const renameQueue = (queueId, queueName) => {
    const newQueueNameOrNull = document.querySelector("#new_queue_name");
    if (newQueueNameOrNull === null) {
        alert("Имя очереди не может быть пустым");
        return;
    }
    const newQueueName = newQueueNameOrNull.value.trim();
    if (newQueueName === "") {
        alert("Имя очереди не может быть пустым или состоять из пробелов");
        return;
    }
    if (newQueueName.length > 99){
        alert("Имя очереди не должно превышать 100 символов");
        return;
    }
    if (newQueueName === queueName.trim()) {
        alert("Новое имя очереди должно отличаться от старого");
        return;
    }
    setSpinnerVisibility(true);
    fetch(`/api/queues/${queueId}/rename-queue`, {method: "PUT", body: newQueueName})
        .then(response => {
            if (response.status !== 204) {
                return Promise.reject();
            }
            location.reload();
        })
        .finally(() => {
            setSpinnerVisibility(false)
        });
};

const setSpinnerVisibility = isVisible => {
    document.getElementById("spinner").style.visibility = isVisible ? "visible" : "hidden";
};
