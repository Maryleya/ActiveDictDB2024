let items = $(".list-wrapper .list-item");
let numItems = items.length;
let perPage = 20;

items.slice(perPage).hide();

$('#pagination-container').pagination({
    items: numItems,
    itemsOnPage: perPage,
    prevText: "Назад",
    nextText: "Дальше",
    onPageClick: function (pageNumber) {
        const showFrom = perPage * (pageNumber - 1);
        const showTo = showFrom + perPage;
        items.hide().slice(showFrom, showTo).show();
    }
});

$(document).ready(function(e) {

    $('.list-item').expander({
        expandText:'Читать далее',
        userCollapseText:'Скрыть',
        slicePoint: 150,
        expandEffect:'slideDown',
        expandSpeed: 250,
        collapseEffect:'slideUp',
        collapseSpeed: 200,
        expandPrefix:'',


    });

});
