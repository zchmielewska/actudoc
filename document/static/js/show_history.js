document.addEventListener("DOMContentLoaded", function() {
    const show_history = document.getElementById("show-history");
    const history = document.getElementById("history")

    show_history.addEventListener("click", function() {
        history.style.display = "block";
    })
})