const setSpinnerVisibility = isVisible => {
    document.getElementById("spinner").style.visibility = isVisible ? "visible" : "hidden";
};

const handleBurgerMenu = () => {
    const nav = document.querySelector("header > nav");
    if (nav.style.display === "") {
        nav.style.display = "block";
    } else {
        nav.style.display = "";
    }
};
