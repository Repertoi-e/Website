var elem = document.querySelector('.windows');
var msnry = new Masonry( elem, {
  itemSelector: '.window_container',
  columnWidth: 300,
  gutter: 10,
  horizontalOrder: true,
  fitWidth: true
});