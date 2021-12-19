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

class DndDesktop {
    // state fields
    static isStarted = false;
    static draggedRow;
    static thumbnailElement;

    // constants
    static THUMBNAIL_OFFSET = {x: -15, y: -5};

    // event handlers
    static onDragStart(dragStartEvent) {
        DndDesktop.isStarted = true;
        DndDesktop.draggedRow = dragStartEvent.currentTarget;

        // trim because there is some random whitespace generated for this value in our templates
        const memberName = DndDesktop.draggedRow.children[1].textContent.trim();
        DndDesktop.createThumbnail(memberName, dragStartEvent);
    }

    static onDragOver(dragOverEvent) {
        // prevent further processing of the event, this way we prevent the browser from overtaking these events
        dragOverEvent.preventDefault();

        // If drag state is not initialized,
        // that means that the user is trying to drag and drop something from outside the app,
        // so just exit
        if (!DndDesktop.isStarted) {
            dragOverEvent.dataTransfer.dropEffect = "none";
            return;
        }

        // forbid trying to drag and drop a row onto itself
        const dropTargetQueueMemberRow = dragOverEvent.currentTarget;
        if (DndDesktop.draggedRow === dropTargetQueueMemberRow) {
            dragOverEvent.dataTransfer.dropEffect = "none";
            return;
        }

        // otherwise, hovering over a valid target
        dragOverEvent.dataTransfer.dropEffect = "move";
        DndCommon.updateHighlight(dragOverEvent.clientY, dropTargetQueueMemberRow);
    }

    static onDragLeave(dragLeaveEvent) {
        // we get dragleave events for different children of the same row, so check for that before doing anything
        if (DndCommon.getQueueMemberRowParent(dragLeaveEvent.fromElement) === DndCommon.getQueueMemberRowParent(dragLeaveEvent.toElement)) {
            return;
        }
        DndCommon.clearHighlight();
    }

    static onDrop(dropEvent) {
        // If drag state is not initialized,
        // that means that the user is trying to drag and drop something from outside the app,
        // so just exit
        if (!DndDesktop.isStarted) {
            return;
        }

        DndCommon.clearHighlight();
        const dropTargetQueueMemberRow = dropEvent.currentTarget;
        DndCommon.dropQueueMemberRow(dropEvent.clientY, DndDesktop.draggedRow, dropTargetQueueMemberRow);
    }

    static onDragEnd() {
        DndDesktop.isStarted = false;
        DndDesktop.removeThumbnail();
    }

    // helper functions
    static createThumbnail(text, dragStartEvent) {
        DndDesktop.thumbnailElement = document.createElement("span");
        DndDesktop.thumbnailElement.textContent = text;
        // hide thumbnail behind the page
        DndDesktop.thumbnailElement.style.position = "absolute";
        DndDesktop.thumbnailElement.style.zIndex = "-1";
        document.body.prepend(DndDesktop.thumbnailElement);
        dragStartEvent.dataTransfer.setDragImage(DndDesktop.thumbnailElement, DndDesktop.THUMBNAIL_OFFSET.x, DndDesktop.THUMBNAIL_OFFSET.y);
    }

    static removeThumbnail() {
        removeElementFromDom(DndDesktop.thumbnailElement);
    }
}

// for dragging queue members on mobile devices using Touch API, because HTML5 DND API is not available there
class DndMobile {
    // state fields
    static touchId = null;
    static draggedRow;
    static thumbnailElement;
    static originalScrollBehavior;

    // constants
    static UPDATE_FPS = 60;
    static UPDATE_MSPF = 1000 / DndMobile.UPDATE_FPS; // milliseconds per frame
    static TOUCH_SCROLL_SPEED = 0.01; // in percentages of screen height
    static TOUCH_SCROLL_SENSITIVITY_RANGE = 50; // in pixels

    // event handlers
    static onTouchStart(touchStartEvent) {
        console.log("dnd touchstart");
        const newTouchId = touchStartEvent.changedTouches[0].identifier;
        // do not handle multiple simultaneous touches
        if (DndMobile.touchId !== null) {
            return;
        }
        DndMobile.touchId = newTouchId;
        DndMobile.draggedRow = touchStartEvent.currentTarget.parentElement;
        // trim because there is some random whitespace generated for this value in our templates
        DndMobile.createThumbnail(DndMobile.draggedRow.children[1].textContent.trim());

        // disable smooth scrolling, because we are going to be controlling the scrolling animation
        DndMobile.originalScrollBehavior = document.documentElement.style.scrollBehavior;
        document.documentElement.style.scrollBehavior = 'auto';

        DndMobile.updatePerFrame();
    }

    static onTouchMove(touchMoveEvent) {
        touchMoveEvent.preventDefault(); // prevent the browser from reacting to this event (e.g. scrolling the page)
    }

    static onTouchEnd(touchEndEvent) {
        const touchId = touchEndEvent.changedTouches[0].identifier;
        // do not handle multiple simultaneous touches
        if (touchId !== DndMobile.touchId) {
            return;
        }
        DndMobile.touchId = null;

        DndCommon.clearHighlight();
        DndMobile.removeThumbnail();
        // restore original scroll behavior
        document.documentElement.style.scrollBehavior = DndMobile.originalScrollBehavior;

        const dropTargetQueueMemberRow = DndMobile.getQueueMemberRowAtPosition(CursorPositionMobile.screenPosition);
        // do nothing if dropping on the same row or not a row element at all
        if (dropTargetQueueMemberRow === null || DndMobile.draggedRow === dropTargetQueueMemberRow) {
            return;
        }

        DndCommon.dropQueueMemberRow(CursorPositionMobile.screenPosition.y, DndMobile.draggedRow, dropTargetQueueMemberRow);
    }

    // helpers
    static createThumbnail(text) {
        DndMobile.thumbnailElement = document.createElement("span");
        DndMobile.thumbnailElement.textContent = text;
        DndMobile.thumbnailElement.style.userSelect = "none";
        DndMobile.thumbnailElement.style.position = "absolute";
        DndMobile.updateThumbnail();
        document.body.prepend(DndMobile.thumbnailElement);
    }

    static updateThumbnail() {
        DndMobile.thumbnailElement.style.top = `${CursorPositionMobile.pagePosition.y}px`;
        // use Math.max to prevent thumbnail from going off the right edge of the screen
        DndMobile.thumbnailElement.style.right = `${Math.max(0, window.innerWidth - CursorPositionMobile.pagePosition.x)}px`;
    }

    static removeThumbnail() {
        removeElementFromDom(DndMobile.thumbnailElement);
    }

    static getQueueMemberRowAtPosition(position) {
        const hits = document.elementsFromPoint(position.x, position.y);
        for (const hit of hits) {
            const queueMemberRowParent = DndCommon.getQueueMemberRowParent(hit);
            if (queueMemberRowParent !== null) {
                return queueMemberRowParent;
            }
        }
        return null;
    }

    static scrollAtEdges() {
        const proximity = CursorPositionMobile.isCloseToScreenEdge(DndMobile.TOUCH_SCROLL_SENSITIVITY_RANGE);
        switch (proximity) {
            case CursorEdgeProximity.CloseToTop:
                window.scrollBy(0, -DndMobile.TOUCH_SCROLL_SPEED * window.innerHeight);
                break;
            case CursorEdgeProximity.CloseToBottom:
                // do not scroll past the bottom of the page
                if (!CursorPositionMobile.isCloseToPageBottom(DndMobile.TOUCH_SCROLL_SENSITIVITY_RANGE)) {
                    window.scrollBy(0, DndMobile.TOUCH_SCROLL_SPEED * window.innerHeight);
                } else {
                    // stick to the bottom in order to avoid certain visual bugs
                    window.scrollBy(0, document.body.parentElement.offsetHeight - window.scrollY - window.innerHeight);
                }
                break;
            case CursorEdgeProximity.NotClose:
                // do nothing
                break;
        }
    }

    static updatePerFrame() {
        // stop per-frame updates if DND finished
        if (DndMobile.touchId == null) {
            return;
        }
        DndMobile.updateThumbnail();
        DndMobile.scrollAtEdges();
        const dropTargetQueueMemberRow = DndMobile.getQueueMemberRowAtPosition(CursorPositionMobile.screenPosition);
        if (dropTargetQueueMemberRow !== null && dropTargetQueueMemberRow !== DndMobile.draggedRow) {
            DndCommon.updateHighlight(CursorPositionMobile.screenPosition.y, dropTargetQueueMemberRow);
        } else {
            DndCommon.clearHighlight();
        }
        setTimeout(DndMobile.updatePerFrame, DndMobile.UPDATE_MSPF);
    }
}

class DndCommon {
    // state fields
    static prevHighlightedRow = null;

    // constants
    static HIGHLIGHT_UPPER_CLASS = "drop-to-upper-half";
    static HIGHLIGHT_LOWER_CLASS = "drop-to-lower-half";
    static QUEUE_MEMBER_ROW_ID_PATTERN = "queue-member-";

    // helper functions
    static updateHighlight(cursorPositionY, dropTarget) {
        switch (inWhatHalf(cursorPositionY, dropTarget)) {
            case InWhatHalfResult.Top:
                // make sure to do the minimum number of operations on classList in order to avoid flickering
                if (!dropTarget.classList.contains(DndCommon.HIGHLIGHT_UPPER_CLASS)) {
                    dropTarget.classList.add(DndCommon.HIGHLIGHT_UPPER_CLASS);
                }
                if (dropTarget.classList.contains(DndCommon.HIGHLIGHT_LOWER_CLASS)) {
                    dropTarget.classList.remove(DndCommon.HIGHLIGHT_LOWER_CLASS);
                }
                break;
            case InWhatHalfResult.Bottom:
                // make sure to do the minimum number of operations on classList in order to avoid flickering
                if (dropTarget.classList.contains(DndCommon.HIGHLIGHT_UPPER_CLASS)) {
                    dropTarget.classList.remove(DndCommon.HIGHLIGHT_UPPER_CLASS);
                }
                if (!dropTarget.classList.contains(DndCommon.HIGHLIGHT_LOWER_CLASS)) {
                    dropTarget.classList.add(DndCommon.HIGHLIGHT_LOWER_CLASS);
                }
                break;
            case InWhatHalfResult.None:
                // do nothing, because this still happens sometimes,
                // but it's impossible to catch this happening visually, so this won't ever affect the user
                break;
        }
        // if the highlighted row didn't change, then we have already taken care of clearing the previous highlight above
        if (DndCommon.prevHighlightedRow !== null && DndCommon.prevHighlightedRow !== dropTarget) {
            DndCommon.prevHighlightedRow.classList.remove(DndCommon.HIGHLIGHT_UPPER_CLASS, DndCommon.HIGHLIGHT_LOWER_CLASS);
        }
        DndCommon.prevHighlightedRow = dropTarget;
    }

    static clearHighlight() {
        if (DndCommon.prevHighlightedRow !== null) {
            DndCommon.prevHighlightedRow.classList.remove(DndCommon.HIGHLIGHT_UPPER_CLASS, DndCommon.HIGHLIGHT_LOWER_CLASS);
            DndCommon.prevHighlightedRow = null;
        }
    }

    static dropQueueMemberRow(cursorPositionY, draggedQueueMemberRow, dropTargetQueueMemberRow) {
        let insertedBefore;
        switch (inWhatHalf(cursorPositionY, dropTargetQueueMemberRow)) {
            case InWhatHalfResult.Top:
                insertBefore(draggedQueueMemberRow, dropTargetQueueMemberRow);
                insertedBefore = true;
                break;
            case InWhatHalfResult.Bottom:
                insertAfter(draggedQueueMemberRow, dropTargetQueueMemberRow);
                insertedBefore = false;
                break;
            case InWhatHalfResult.None:
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

    static getQueueMemberRowParent(child) {
        while (child !== null) {
            if (child.id.startsWith(DndCommon.QUEUE_MEMBER_ROW_ID_PATTERN)) {
                return child;
            }
            child = child.parentElement;
        }
        return null;
    }
}

const CursorEdgeProximity = {
    CloseToTop: 1,
    CloseToBottom: 2,
    NotClose: 3,
};

class CursorPositionMobile {
    static currentTouchId = null;
    static screenPosition = {x: 0, y: 0};

    static init() {
        // passing true as the third parameter ensures that our handler gets called first;
        // we don't need to do it for the rest of the handlers though
        document.addEventListener("touchstart", CursorPositionMobile.onTouchStart, true);
        document.addEventListener("touchmove", CursorPositionMobile.onTouchMove);
        document.addEventListener("touchend", CursorPositionMobile.onTouchEnd);
    }

    static get pagePosition() {
        return {x: CursorPositionMobile.screenPosition.x + window.scrollX, y: CursorPositionMobile.screenPosition.y + window.scrollY};
    }

    static onTouchStart(touchStartEvent) {
        // track position only for one finger
        if (CursorPositionMobile.currentTouchId === null) {
            const touch = touchStartEvent.changedTouches[0];
            CursorPositionMobile.currentTouchId = touch.identifier;
            CursorPositionMobile.screenPosition.x = touch.clientX;
            CursorPositionMobile.screenPosition.y = touch.clientY;
        }
    }

    static onTouchMove(touchMoveEvent) {
        // track position only for one finger
        const touch = touchMoveEvent.changedTouches[0];
        if (CursorPositionMobile.currentTouchId !== touch.identifier) {
            return;
        }
        CursorPositionMobile.screenPosition.x = touch.clientX;
        CursorPositionMobile.screenPosition.y = touch.clientY;
    }

    static onTouchEnd(touchEndEvent) {
        const touch = touchEndEvent.changedTouches[0];
        if (CursorPositionMobile.currentTouchId === touch.identifier) {
            CursorPositionMobile.currentTouchId = null;
        }
    }

    static isCloseToScreenEdge(range) {
        if (CursorPositionMobile.screenPosition.y < range) {
            return CursorEdgeProximity.CloseToTop;
        }
        if (window.innerHeight - CursorPositionMobile.screenPosition.y < range) {
            return CursorEdgeProximity.CloseToBottom;
        }
        return CursorEdgeProximity.NotClose;
    }

    static isCloseToPageBottom(range) {
        return CursorPositionMobile.pagePosition.y >= document.body.parentElement.offsetHeight - range;
    }
}

// miscellaneous helper functions
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

const removeElementFromDom = element => {
    element.parentElement.removeChild(element);
}

const InWhatHalfResult = {
    Top: 1,
    Bottom: 2,
    None: 3,
};

const inWhatHalf = (positionY, element) => {
    const elementRect = element.getBoundingClientRect();
    const elementMidPoint = elementRect.top + element.clientHeight / 2;
    if (isBetween(Math.floor(elementRect.top), positionY, elementMidPoint)) {
        return InWhatHalfResult.Top;
    }
    if (isBetween(elementMidPoint, positionY, Math.ceil(elementRect.bottom))) {
        return InWhatHalfResult.Bottom;
    }
    return InWhatHalfResult.None;
};

(() => {
    document.getElementById("new_queue_name").addEventListener("keydown", event => {
        if (event.key === "Enter") {
            document.getElementById("save_queue_name_button").click();
        }
    });

    CursorPositionMobile.init();
})();
