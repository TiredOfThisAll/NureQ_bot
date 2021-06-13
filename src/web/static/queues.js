const deleteQueue = queueId => {
    const isConfirmed = confirm(`Вы уверены, что хотите удалить очередь с ID: ${queueId}`);
    if (!isConfirmed) {
        return;
    }
    setSpinnerVisibility(true);
    fetch(`/api/queues/${queueId}`, {method: "DELETE"})
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