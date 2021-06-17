const deleteMember = (queueId, queueName, queueMemberName, queueMemberUserId) => {
    const isConfirmed = confirm(`Вы уверены, что хотите удалить ${queueMemberName} из ${queueName} очереди`);
    if (!isConfirmed) {
        return;
    }
    setSpinnerVisibility(true);
    fetch(`/api/queues/${queueId}/members/${queueMemberUserId}`, {method: "DELETE"})
        .then(response => {
            if (response.status !== 204) {
                response.text().then(alert);
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
                response.text().then(alert);
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
                response.text().then(alert);
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
                response.text().then(alert);
                return Promise.reject();
            }
            location.reload();
        })
        .finally(() => {
            setSpinnerVisibility(false)
        });
};

const renameQueue = (queueId, originalQueueName) => {
    const newQueueName = document.querySelector("#new_queue_name").value.trim();
    if (newQueueName === "") {
        alert("Имя очереди не может быть пустым или состоять из пробелов");
        return;
    }
    if (newQueueName.length > 99){
        alert("Имя очереди не должно превышать 100 символов");
        return;
    }
    if (newQueueName === originalQueueName) {
        alert("Новое имя очереди должно отличаться от старого");
        return;
    }
    setSpinnerVisibility(true);
    fetch(`/api/queues/${queueId}/name`, {method: "PUT", body: newQueueName})
        .then(response => {
            if (response.status === 409) {
                alert(`Имя '${newQueueName}' уже используется`);
                return;
            }
            if (response.status !== 204) {
                response.text().then(alert);
                return Promise.reject();
            }
            location.reload();
        })
        .finally(() => {
            setSpinnerVisibility(false)
        });
};

const handleQueueNameChange = () => {
    document.getElementById("new_queue_input_subtext").hidden = false;

    const saveQueueNameButton = document.getElementById("save_queue_name_button");
    saveQueueNameButton.classList.remove("btn-outline-primary");
    saveQueueNameButton.classList.add("btn-primary");
};

const handleQueueMemberRowDragstart = event => {
    event.currentTarget.ondragover = null;
    event.dataTransfer.setData("text/plain", event.currentTarget.id);
};

const handleQueueMemberRowDragover = event => {
    event.preventDefault(); // prevent additional event processing for this event

    const dropTargetQueueMemberRow = event.currentTarget;
    const draggedQueueMemberRowId = event.dataTransfer.getData("text/plain");
    console.log(draggedQueueMemberRowId)
    if (dropTargetQueueMemberRow.id === draggedQueueMemberRowId) {
        return;
    }

    event.dataTransfer.dropEffect = "move";

    const isInUpperHalf = getIsInUpperHalf(event.clientY, dropTargetQueueMemberRow);
    if (isInUpperHalf) {
        dropTargetQueueMemberRow.classList.remove("drop-to-lower-half");
        dropTargetQueueMemberRow.classList.add("drop-to-upper-half");
    } else {
        dropTargetQueueMemberRow.classList.remove("drop-to-upper-half");
        dropTargetQueueMemberRow.classList.add("drop-to-lower-half");
    }
};

const handleQueueMemberRowDragleave = event => {
    const dropTargetQueueMemberRow = event.currentTarget;
    dropTargetQueueMemberRow.classList.remove("drop-to-lower-half", "drop-to-upper-half");
}

const handleQueueMemberRowDragend = event => {
    const draggedQueueMemberRowId = event.dataTransfer.getData("text/plain");
    const draggedQueueMemberRow = document.getElementById(draggedQueueMemberRowId);
    draggedQueueMemberRow.addEventListener("dragover", handleQueueMemberRowDragover);
}

const handleQueueMemberRowDrop = event => {
    event.preventDefault(); // prevent additional event processing for this event

    const draggedQueueMemberRowId = event.dataTransfer.getData("text/plain");
    const draggedQueueMemberRow = document.getElementById(draggedQueueMemberRowId);
    const dropTargetQueueMemberRow = event.currentTarget;

    const isInUpperHalf = getIsInUpperHalf(event.clientY, dropTargetQueueMemberRow);
    if (isInUpperHalf) {
        insertBefore(draggedQueueMemberRow, dropTargetQueueMemberRow);
    } else {
        insertAfter(draggedQueueMemberRow, dropTargetQueueMemberRow.nextSibling);
    }
    dropTargetQueueMemberRow.classList.remove("drop-to-lower-half", "drop-to-upper-half");
};

const isBetween = (min, value, max) => value >= min && value < max;

const insertAfter = (elementToInsert, referenceElement) => {
    referenceElement.parentNode.insertBefore(elementToInsert, referenceElement.nextSibling);
};

const insertBefore = (elementToInsert, referenceElement) => {
    referenceElement.parentNode.insertBefore(elementToInsert, referenceElement);
};

const getIsInUpperHalf = (positionY, element) => {
    const elementRect = element.getBoundingClientRect();

    const elementMidPoint = elementRect.top + element.clientHeight / 2;
    return isBetween(elementRect.top, positionY, elementMidPoint);
};

(() => {
    document.getElementById("new_queue_name").addEventListener("keydown", event => {
        if (event.key === "Enter") {
            document.getElementById("save_queue_name_button").click();
        }
    });
})();
