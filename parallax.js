const parallaxElements = document.querySelectorAll(".parallax");
const parallaxElementsSpecial = document.querySelectorAll(".parallax_special");

window.addEventListener("scroll", () => {
    let scroll = window.pageYOffset;

    parallaxElements.forEach(e => {
        let speed = e.dataset.speed;
        e.style.transform = `translate(-50%, -50%) translateY(${scroll * speed}px)`;
    });

    parallaxElementsSpecial.forEach(e => {
        let speed = e.dataset.speed;
        e.style.transform = `translateY(${scroll * speed}px)`;
    });
});