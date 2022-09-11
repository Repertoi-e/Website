// Handle the projects view in the about page

$(document).ready(function () {
    $(".projects__windows__window").hover(function () {
        $(this).find("img").css("opacity", "0.8");
        $(this).find("p").slideDown(100, function () { });
    }, function () {
        $(this).find("img").css("opacity", "1");

        // Must match $screen-md-min: 768px;  in scss/abstracts/_breakpoints.scss
        if (window.matchMedia("(min-width: 768px)")) {
            $(this).find("p").slideUp(100, function () { });
        }
    });
});
