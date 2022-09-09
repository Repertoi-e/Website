//
// Blog annotations logic:
//

// Collapse all explanatory content initially
$(".annotation_content").hide()

$(document).ready(function () {
    // Hover logic for each "class" of notes (multiple can be linked!) 
    $(".annotation").hover(function () {
        id_class = $(this).attr("class").split(" ")[1]
        $("." + id_class).addClass("annotation_hover")

        t = $("." + id_class).last().find(".annotation_link").text()
        $(".annotation_preview_number").text(t)

        t = $("." + id_class).last().find(".annotation_content_raw").html()
        $(".annotation_preview_content").html(t)

        $(".annotation_preview").slideDown(100, function () { })
    }, function () {
        id_class = $(this).attr("class").split(" ")[1]
        $("." + id_class).removeClass("annotation_hover")
        $(".annotation_preview").slideUp(100, function () { })
    })

    // Hide all superscript numbers...
    $(".annotation_content").each(function (index) {
        $(this).parent().find(".annotation_link").hide()
    })
    // ... but show only on the last linked note.
    $(".annotation_content").each(function (index) {
        id_class = $(this).parent().attr("class").split(" ")[1]
        $("." + id_class).last().find(".annotation_link").show()
    })

    $(".annotation").click(function (index) {
        id_class = $(this).attr("class").split(" ")[1]
        $("." + id_class).last().find(".annotation_content").toggle()
    })
});



