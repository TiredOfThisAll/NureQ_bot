const deleteQueue = (queueId) => {
    let isDelete = confirm(`Чел, а ты уверен вообще? Ты вообще-то хочешь удалить очередь с идишником ${queueId}`);
    if (!isDelete) {
        return;
    }
    fetch(`/queues/${queueId}`, {method: "DELETE"})
        .then(response => {
            if (response.status !== 201) {
                return Promise.reject();
            }
            location.reload();
        });
};
