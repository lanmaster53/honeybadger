function flash(msg) {
    $('#flash').html(msg);
    $('#flash').css('visibility', 'visible');
    setTimeout(function() { $('#flash').css('visibility', 'hidden'); }, 5000);
}

function copy2clip(s) {
    var dummy = document.createElement("input");
    document.body.appendChild(dummy);
    dummy.setAttribute("id", "dummy_id");
    document.getElementById("dummy_id").value = s;
    dummy.select();
    try {
        document.execCommand("copy");
    } catch (e) {
        console.log("Copy failed.");
    }
    document.body.removeChild(dummy);
    flash("Link copied.");
}

$(document).ready(function() {

    // flash on load if needed
    if($('#flash').html().length > 0) {
        flash($('#flash').html());
    }

});
