// Static variables
const NUMB_IMAGES = 7;
const FADE_TIME = 300;
const SLIDE_TIME = 5000
const background = $('.cover-image');

// Get background images
let images = [];
for (var j = 0; j < NUMB_IMAGES; j++) {
  images.push("../../static/img/bg" + j.toString() + ".jpeg" );
}

// Preload all images into cache
function preload(){
  images.forEach(function(elem) {
    im = new Image();
    im.src = elem;
  });
}
preload();

// Run image slideshow
let i = 0;
setInterval(function() {
  // background.fadeTo(FADE_TIME, 0.9);
  background.css('background-image', 'url(' + images[i] + ')');
  // setTimeout(function() { background.fadeTo(FADE_TIME, 1); }, FADE_TIME);
  i = i + 1;
  if (i == NUMB_IMAGES) {
    i =  0;
  }
}, SLIDE_TIME);


// Dropdown handler
$("#index-dropdown").click(function() {
  $("html, body").animate({ scrollTop: window.innerHeight }, 600);
});
