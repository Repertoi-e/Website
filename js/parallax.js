const contentContainer = document.querySelector("body");
const speeds = [0.2, 0.7, 0.7, 1]; /* @Hardcoded for index page: me, clouds, clouds, bg */

const bgPositions = getComputedStyle(contentContainer).backgroundPosition.replace(/^\s+|\s+$/g, "").split(/\s*,\s*/);

function update_scroll() {
    let scroll = window.pageYOffset;

    let result = "";

    bgPositions.forEach((bg, i) => {
        let coords = bg.replace(/[^0-9-]/g, ' ').split(/ +/).slice(0, 2).map(x => Number(x));

        let speed = speeds[i];

        result += coords[0] + "px ";
        result += (coords[1] + scroll * speed) + "px";

        if (i != bgPositions.length - 1) {
            result += ", ";
        }
    });
    contentContainer.style.backgroundPosition = result;
}

/* Update it the first time the page loads */
update_scroll();
window.addEventListener("scroll", update_scroll);
window.addEventListener('resize', update_scroll);
