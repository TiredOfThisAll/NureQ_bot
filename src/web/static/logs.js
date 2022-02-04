const toggleExpandHideLog = event => {
    // don't react to clicks if the user is trying to select text
    const currentTextSelected = window.getSelection().toString();
    if (currentTextSelected !== "") {
        return;
    }

    const targetClassName = "short-log";
    if (event.currentTarget.classList.contains(targetClassName)) {
        event.currentTarget.classList.remove(targetClassName);
    } else {
        event.currentTarget.classList.add(targetClassName);
    }
};
