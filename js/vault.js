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

$(window).resize(function () {
    // Must match $screen-md-min: 768px;  in scss/abstracts/_breakpoints.scss
    if ($(window).width() >= 768) {
        $(".projects__windows__window").find("p").hide();
    } else {
        $(".projects__windows__window").find("p").show();
    }
    $grid.masonry("layout");
});

$(document).ready(function () {
    $(".projects__windows__window").hover(function () {
        $(this).find(".projects__windows__window__overlay").fadeTo(100, 0.5);
        $(this).find("p").slideDown(100, function () { });
    }, function () {
        $(this).find(".projects__windows__window__overlay").fadeTo(100, 0);
        // Must match $screen-md-min: 768px;  in scss/abstracts/_breakpoints.scss
        if ($(window).width() >= 768) {
            $(this).find("p").slideUp(100, function () { });
        }
    });
});

var selected = "#vault-game-dev"

function update_directory() {
    $(".vault-programming-option").css("text-decoration", "none")
    $(".vault-programming-option").css("font-weight", "normal")
    $(selected).css("text-decoration", "underline")
    $(selected).css("font-weight", "bold")
}

$("#vault-game-dev").click(function() {
    selected ="#vault-game-dev"
    update_directory()
});

$("#vault-math-ml").click(function() {
    selected = "#vault-math-ml"
    update_directory()
});

$("#vault-cpp").click(function() {
    selected = "#vault-cpp"
    update_directory()
});

update_directory()

