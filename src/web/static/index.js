const setSpinnerVisibility = isVisible => {
    document.getElementById("spinner").style.visibility = isVisible ? "visible" : "hidden";
};

const handleBurgerMenu = () => {
    const nav = document.querySelector("header > nav");
    if (nav.style.height === "") {
        nav.style.height = "160px";
    } else {
        nav.style.height = "";
    }
};
