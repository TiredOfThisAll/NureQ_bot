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

    // clear highlighting
    dropTargetQueueMemberRow.classList.remove("drop-to-lower-half", "drop-to-upper-half");

    dropQueueMemberRow(event.clientY, draggedQueueMemberRow, dropTargetQueueMemberRow);
};

const dropQueueMemberRow = (cursorPositionY, draggedQueueMemberRow, dropTargetQueueMemberRow) => {
    let insertedBefore;
    if (isInUpperHalf(cursorPositionY, dropTargetQueueMemberRow)) {
        insertBefore(draggedQueueMemberRow, dropTargetQueueMemberRow);
        insertedBefore = true;
    } else if (isInLowerHalf(cursorPositionY, dropTargetQueueMemberRow)) {
        insertAfter(draggedQueueMemberRow, dropTargetQueueMemberRow);
        insertedBefore = false;
    } else {
        return;
    }
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

let dragThumbnailElement = null;
let prevHighlightedRow = null;
let mobileDraggedElement = null;
let currentTouchId = null;

const updateDragThumbnailElementPosition = cursorPosition => {
    // make sure to use document coordinates instead of screen coordinates
    dragThumbnailElement.style.top = `${cursorPosition.y}px`;
    // TODO: comment about Math.max
    dragThumbnailElement.style.right = `${Math.max(0, window.innerWidth - cursorPosition.x)}px`;
};

const handleQueueMemberRowTouchstart = event => {
    // do not handle multiple touches at once
    if (currentTouchId !== null && event.changedTouches[0].identifier !== currentTouchId) {
        return;
    }
    currentTouchId = event.changedTouches[0].identifier;
    mobileDraggedElement = event.currentTarget.parentElement;
    // create drag thumbnail
    dragThumbnailElement = document.createElement("span");
    dragThumbnailElement.textContent = mobileDraggedElement.children[1].textContent.trim();
    dragThumbnailElement.style.userSelect = "none";
    dragThumbnailElement.style.position = "absolute";
    globalCursorPagePosition.x = event.changedTouches[0].pageX;
    globalCursorPagePosition.y = event.changedTouches[0].pageY;
    globalCursorPosition.x = event.changedTouches[0].clientX;
    globalCursorPosition.y = event.changedTouches[0].clientY;
    updateDragThumbnailElementPosition(globalCursorPagePosition);
    document.body.prepend(dragThumbnailElement);
};

const TOUCH_SCROLL_SPEED = window.innerHeight * 0.01;
const TOUCH_SCROLL_SENSITIVITY_RANGE = 50;

const isCloseToScreenEdge = cursorPosition => {
    if (cursorPosition.y < TOUCH_SCROLL_SENSITIVITY_RANGE) {
        return "close_to_top_edge";
    }
    if (window.innerHeight - cursorPosition.y < TOUCH_SCROLL_SENSITIVITY_RANGE) {
        return "close_to_bottom_edge";
    }
    return "not_close";
};

const handleQueueMemberRowTouchmove = event => {
    event.preventDefault(); // prevent the browser from reacting to gestures, while the user is drag-n-dropping

    // do not handle multiple touches at once
    if (currentTouchId !== null && event.changedTouches[0].identifier !== currentTouchId) {
        return;
    }
};

const handleQueueMemberRowTouchend = event => {
    // do not handle multiple touches at once
    if (currentTouchId !== null && event.changedTouches[0].identifier !== currentTouchId) {
        return;
    }
    currentTouchId = null;
    // clear previous highlight
    if (prevHighlightedRow !== null) {
        prevHighlightedRow.classList.remove("drop-to-upper-half", "drop-to-lower-half");
    }

    // remove drag thumbnail
    dragThumbnailElement.parentElement.removeChild(dragThumbnailElement);
    dragThumbnailElement = null;

    const draggedQueueMemberRow = event.currentTarget.parentElement;
    const cursorPosition = getCursorPositionForTouchEvent(event);
    const dropTargetQueueMemberRow = getQueueMemberRowUnderCursor(cursorPosition);
    // do nothing if dropping on the same row or not a row element at all
    if (dropTargetQueueMemberRow === null || draggedQueueMemberRow === dropTargetQueueMemberRow) {
        return;
    }

    dropQueueMemberRow(cursorPosition.y, draggedQueueMemberRow, dropTargetQueueMemberRow);
};

const getCursorPositionForTouchEvent = event => { // in screen coordinates
    return {x: event.changedTouches[0].clientX, y: event.changedTouches[0].clientY};
};

const getQueueMemberRowUnderCursor = cursorPosition => {
    const hits = document.elementsFromPoint(cursorPosition.x, cursorPosition.y);
    for (const hit of hits) {
        let result = hit;
        while (result !== null) {
            if (result.id.startsWith("queue-member-")) {
                return result;
            }
            result = result.parentElement;
        }
    }
    return null;
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

const globalCursorPosition = {x: 0, y: 0};
const globalCursorPagePosition = {x: 0, y: 0};

const trackCursorPosition = touchMoveEvent => {
    if (currentTouchId !== null && event.changedTouches[0].identifier !== currentTouchId) {
        return;
    }
    const p = getCursorPositionForTouchEvent(touchMoveEvent);
    globalCursorPosition.x = p.x;
    globalCursorPosition.y = p.y;
    globalCursorPagePosition.x = touchMoveEvent.changedTouches[0].pageX;
    globalCursorPagePosition.y = touchMoveEvent.changedTouches[0].pageY;
};

const scrollAtEdgesWhenDragNDroppingOnMobile = () => {
    if (dragThumbnailElement !== null) {
        const cursorPosition = globalCursorPosition;
        const proximity = isCloseToScreenEdge(cursorPosition);
        switch (proximity) {
            case "close_to_top_edge":
                window.scrollBy(0, -TOUCH_SCROLL_SPEED);
                break;
            case "close_to_bottom_edge":
                if (globalCursorPagePosition.y < document.body.parentElement.offsetHeight - 50) {
                    window.scrollBy(0, TOUCH_SCROLL_SPEED);
                }
                break;
            case "not_close":
                // do nothing
                break;
        }

        // move drag thumbnail
        updateDragThumbnailElementPosition(globalCursorPagePosition);

        // clear previous highlight
        if (prevHighlightedRow !== null) {
            prevHighlightedRow.classList.remove("drop-to-upper-half", "drop-to-lower-half");
        }

        // highlight drop area
        const dropTargetQueueMemberRow = getQueueMemberRowUnderCursor(cursorPosition);
        const sourceQueueMemberRow = mobileDraggedElement;
        // skip highlighting if hovering over something other than a queue member row or over the same row
        if (dropTargetQueueMemberRow !== null && dropTargetQueueMemberRow !== sourceQueueMemberRow) {
            if (isInUpperHalf(cursorPosition.y, dropTargetQueueMemberRow)) {
                dropTargetQueueMemberRow.classList.add("drop-to-upper-half");
                prevHighlightedRow = dropTargetQueueMemberRow;
            } else if (isInLowerHalf(cursorPosition.y, dropTargetQueueMemberRow)) {
                dropTargetQueueMemberRow.classList.add("drop-to-lower-half");
                prevHighlightedRow = dropTargetQueueMemberRow;
            }
        }
    }

    setTimeout(scrollAtEdgesWhenDragNDroppingOnMobile, 15);
};

(() => {
    document.getElementById("new_queue_name").addEventListener("keydown", event => {
        if (event.key === "Enter") {
            document.getElementById("save_queue_name_button").click();
        }
    });

    document.addEventListener("scroll", () => {
        globalCursorPagePosition.y = window.scrollY + globalCursorPosition.y;
    });
    document.addEventListener("touchmove", trackCursorPosition);

    document.documentElement.style.scrollBehavior = 'auto';
    scrollAtEdgesWhenDragNDroppingOnMobile();
})();
