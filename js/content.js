$(document).ready(function () {
    $(".content__block").find("p").hide();

    var $grid = $(".content").masonry({
        itemSelector: ".content__block",
        columnWidth: ".content__block",
        percentPosition: true,
        originLeft: false
    }); 

    $grid.imagesLoaded().progress(function () {
        $grid.masonry("layout");
    }); 

    let videoElements = document.querySelectorAll('video');
    for(let video of videoElements){
        video.addEventListener('loadeddata', (event) => {
            $grid.masonry("layout");
        });
    }

    $(".content__block").hover(function () {
        $(this).find(".overlay").fadeTo(100, 0.5);
    }, function () {
        $(this).find(".overlay").fadeTo(100, 0);
    });
});
