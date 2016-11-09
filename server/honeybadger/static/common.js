function flash(msg) {
    $('#flash').html(msg);
    $('#flash').css('visibility', 'visible');
    setTimeout(function() { $('#flash').css('visibility', 'hidden'); }, 5000);
}

$(document).ready(function() {

    // flash on load if needed
    if($('#flash').html().length > 0) {
        flash($('#flash').html());
    }

});
