const contentContainer = document.querySelector(".content");

const backgrounds = getComputedStyle(contentContainer).backgroundPosition.replace(/^\s+|\s+$/g,"").split(/\s*,\s*/);

const speeds = [0.2, 0.7, 0.7, 1]; // me, clouds, clouds, bg

window.addEventListener("scroll", () => {
    let scroll = window.pageYOffset;

    let result = "";

    backgrounds.forEach((bg, i) => {
        let coords = bg.replace(/[^0-9-]/g,' ').split(/ +/).slice(0, 2).map(x => Number(x));
        
        let speed = speeds[i];
        
        result += coords[0] + "px ";
        result += (coords[1] + scroll * speed) + "px";

        if (i != backgrounds.length - 1) {
            result += ", "; 
        }
    });
    contentContainer.style.backgroundPosition = result;
});