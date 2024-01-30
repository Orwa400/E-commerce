// static/script.js

$(document).ready(function () {
    // Example: Hightlight the selected navigation item
    $('nav a').on('click', function () {
        $('nav a').removeClass('active');
        $(this).addClass('active');
    });
});