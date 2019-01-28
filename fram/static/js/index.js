$("#index-dropdown").click(function() {
  $("html, body").animate({ scrollTop: window.innerHeight }, 600);
});

const NUMB_IMAGES = 7;
const FADE_TIME = 20;
const background = $('.cover-image');

url = '../../static/img/bg2.jpeg'

background.css('background-image', 'url(' + url + ')');

let i = 0;
setInterval(function() {
  background.fadeTo(FADE_TIME, 0.9);
  setTimeout(function() { background.css('background-image', 'url(' + "../../static/img/bg" + i.toString() + ".jpeg" + ')') }, FADE_TIME);
  setTimeout(function() { background.fadeTo(FADE_TIME, 1); }, FADE_TIME);
  i = i + 1;
  if (i == NUMB_IMAGES) {
    i =  0;
  }
}, 3000);
