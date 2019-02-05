// Static variables
const NUMB_IMAGES = 7;
const FADE_TIME = 300;
const SLIDE_TIME = 3000
const background = $('.inner-div');

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

// Dropdown handler
$("#index-dropdown").click(function() {
  let secondPagePos = $(".second-page").offset().top;
  $("html, body").animate({ scrollTop: secondPagePos }, 600);
});

// Init variables
let i = 0;
let pause = false;
let win = $(window);

// TODO Stop slideshow when page-tab is not active
// win.blur(function() {
//   if (!( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) )){
//     console.log("blur");
//     pause = true;
//   }
// });
// win.focus(function() {
//   if (!( /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) )){
//     console.log("focus");
//     pause = false;
//   }
// });

// Stop slideshow on scroll-down
win.scroll(function() {
  if ( ( win.scrollTop() + 0.4 * win.innerHeight() ) > window.innerHeight ) {
    pause = true;
    $('.second-page').css('background-color', 'rgba(245, 245, 245, 0.7)');
  }
  else{
    pause = false;
    $('.second-page').css('background-color', 'rgba(245, 245, 245, 0.5)');
  }

  if ( ( win.scrollTop() + 0.5 * win.innerHeight() ) > window.innerHeight ) {
    console.log("UP");
  }
  else{
    console.log("DOWN");
  }
});

$('document').ready(function(){

  // Run image slideshow
  setInterval(function() {
    // background.fadeTo(FADE_TIME, 0.9);
    if (!pause){
      background.css('background-image', 'url(' + images[i] + ')');
      // setTimeout(function() { background.fadeTo(FADE_TIME, 1); }, FADE_TIME);
      i = i + 1;
      if (i == NUMB_IMAGES) {
        i =  0;
      }
    }
  }, SLIDE_TIME);
});
