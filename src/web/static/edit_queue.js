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

const renameQueue = (queueId, originalQueueName) => {
    const newQueueName = document.querySelector("#new_queue_name").value.trim();
    if (newQueueName === "") {
        alert("Имя очереди не может быть пустым или состоять из пробелов");
        return;
    }
    if (newQueueName.length > 100){
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
    document.getElementById("new_queue_input_subtext").style.visibility = "visible";

    const saveQueueNameButton = document.getElementById("save_queue_name_button");
    saveQueueNameButton.classList.remove("btn-outline-primary");
    saveQueueNameButton.classList.add("btn-primary");
};

let dragState;

const handleQueueMemberRowDragstart = event => {
    const draggedQueueMemberRow = event.currentTarget;
    dragState = {draggedQueueMemberRowId: draggedQueueMemberRow.id};
    draggedQueueMemberRow.ondragover = null; // prevent dropping row on itself

    // we can't the use tr or td itself for the preview, because the take up too much space visually
    const queueMemberNameCell = draggedQueueMemberRow.querySelector("td:nth-child(2) > span")
    event.dataTransfer.setDragImage(queueMemberNameCell, -15, -15);
};

const handleQueueMemberRowDragover = event => {
    event.preventDefault(); // prevent additional event processing for this event

    // If drag state is not initialized,
    // that means that the user is trying to drag and drop something from outside the app,
    // so just exit
    if (dragState === undefined) {
        event.dataTransfer.dropEffect = "none";
        return;
    }

    // forbid trying to drag and drop a row onto itself
    const dropTargetQueueMemberRow = event.currentTarget;
    if (dragState.draggedQueueMemberRowId === dropTargetQueueMemberRow.id) {
        event.dataTransfer.dropEffect = "none";
        return;
    }

    if (isInUpperHalf(event.clientY, dropTargetQueueMemberRow)) {
        event.dataTransfer.dropEffect = "move";
        dropTargetQueueMemberRow.classList.remove("drop-to-lower-half");
        dropTargetQueueMemberRow.classList.add("drop-to-upper-half");
    } else if (isInLowerHalf(event.clientY, dropTargetQueueMemberRow)) {
        event.dataTransfer.dropEffect = "move";
        dropTargetQueueMemberRow.classList.remove("drop-to-upper-half");
        dropTargetQueueMemberRow.classList.add("drop-to-lower-half");
    } else {
        event.dataTransfer.dropEffect = "none";
    }
};

const handleQueueMemberRowDragleave = event => {
    const dropTargetQueueMemberRow = event.currentTarget;
    dropTargetQueueMemberRow.classList.remove("drop-to-lower-half", "drop-to-upper-half");
}

const handleQueueMemberRowDragend = _event => {
    const draggedQueueMemberRow = document.getElementById(dragState.draggedQueueMemberRowId);
    // after dragging is finished, restore dragover event for the dragged row
    draggedQueueMemberRow.addEventListener("dragover", handleQueueMemberRowDragover);

    dragState = undefined;
};

const handleQueueMemberRowDrop = event => {
    event.preventDefault(); // prevent additional event processing for this event

    // If drag state is not initialized,
    // that means that the user is trying to drag and drop something from outside the app,
    // so just exit
    if (dragState === undefined) {
        return;
    }

    const draggedQueueMemberRow = document.getElementById(dragState.draggedQueueMemberRowId);
    const dropTargetQueueMemberRow = event.currentTarget;

    let insertedBefore;
    if (isInUpperHalf(event.clientY, dropTargetQueueMemberRow)) {
        insertBefore(draggedQueueMemberRow, dropTargetQueueMemberRow);
        insertedBefore = true;
    } else if (isInLowerHalf(event.clientY, dropTargetQueueMemberRow)) {
        insertAfter(draggedQueueMemberRow, dropTargetQueueMemberRow);
        insertedBefore = false;
    } else {
        return;
    }
    dropTargetQueueMemberRow.classList.remove("drop-to-lower-half", "drop-to-upper-half");
    renderQueuePositions();

    const queueId = dropTargetQueueMemberRow.dataset.queueId;
    const body = JSON.stringify({
        movedUserId: Number(draggedQueueMemberRow.dataset.queueMemberUserId),
        targetUserId: Number(dropTargetQueueMemberRow.dataset.queueMemberUserId),
        insertedBefore,
    });
    fetch(`/api/queues/${queueId}/move-queue-member`, {method: "PUT", body})
        .then(response => {
            if (response.status !== 204) {
                response.text().then(responseText => {
                    alert(responseText);
                    location.reload();
                });
                return Promise.reject();
            }
        });
};

const renderQueuePositions = () => {
    document.querySelectorAll("td:first-child > span > span").forEach((td, index) => {
        td.textContent = (index + 1).toString();
    });
};

const isBetween = (min, value, max) => value >= min && value < max;

const insertAfter = (elementToInsert, referenceElement) => {
    referenceElement.parentNode.insertBefore(elementToInsert, referenceElement.nextSibling);
};

const insertBefore = (elementToInsert, referenceElement) => {
    referenceElement.parentNode.insertBefore(elementToInsert, referenceElement);
};

const isInUpperHalf = (positionY, element) => {
    const elementRect = element.getBoundingClientRect();

    const elementMidPoint = elementRect.top + element.clientHeight / 2;
    return isBetween(elementRect.top, positionY, elementMidPoint);
};

const isInLowerHalf = (positionY, element) => {
    const elementRect = element.getBoundingClientRect();

    const elementMidPoint = elementRect.top + element.clientHeight / 2;
    return isBetween(elementMidPoint, positionY, elementRect.bottom);
};

(() => {
    document.getElementById("new_queue_name").addEventListener("keydown", event => {
        if (event.key === "Enter") {
            document.getElementById("save_queue_name_button").click();
        }
    });
})();
