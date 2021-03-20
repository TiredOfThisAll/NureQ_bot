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
        });
};

const setSpinnerVisibility = isVisible => {
    document.getElementById("spinner").style.visibility = isVisible ? "visible" : "hidden";
};
