// Handle the projects view in the about page

$(".projects__windows__window").find("p").hide();

var $grid = $(".projects__windows").masonry({
    itemSelector: ".projects__windows__window",
    ccolumnWidth: ".projects__window__sizer",
    stamp: ".projects__windows__stamp",
    percentPosition: true,
    originLeft: false
});

$grid.imagesLoaded().progress(function () {
    $grid.masonry("layout");
});

$(document).ready(function () {
    $(".projects__windows__window").hover(function () {
        $(this).find(".projects__windows__window__overlay").fadeTo(100, 0.5);
    }, function () {
        $(this).find(".projects__windows__window__overlay").fadeTo(100, 0);
    });
});



