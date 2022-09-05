

$(document).ready(function() {
    // Collapse all explanatory content initially
    $(".annotation_content").hide()

    // Hover logic for each "class" of notes (multiple can be linked!) 
    $(".annotation").hover(function() { 
        id_class = $(this).attr("class").split(" ")[1]
        $("." + id_class).addClass("annotation_hover")
    }, function() {
        id_class = $(this).attr("class").split(" ")[1]
        $("." + id_class).removeClass("annotation_hover")
    })

    // Hide all superscript numbers...
    $(".annotation_content").each(function(index) {
        $(this).parent().find(".annotation_link").hide()
    })
    // ... but show only on the last linked note.
    $(".annotation_content").each(function(index) {
        id_class = $(this).parent().attr("class").split(" ")[1]
        $("." + id_class).last().find(".annotation_link").show()
    })

    $(".annotation").click(function(index) {
        id_class = $(this).attr("class").split(" ")[1]
        $("." + id_class).last().find(".annotation_content").toggle() 
    })
});



