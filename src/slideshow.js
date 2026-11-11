(function () {
  var root = document.querySelector("[data-slideshow]");
  if (!root) return;
  var dataEl = document.getElementById("slide-data");
  if (!dataEl) return;
  var slides = JSON.parse(dataEl.textContent);
  if (!slides.length) return;
  var frame = root.querySelector(".slide-frame");
  var img = root.querySelector(".slide-photo");
  var link = root.querySelector(".slide-link");
  var caption = root.querySelector(".slide-caption a");
  var count = root.querySelector(".slide-count");
  var prev = root.querySelector(".slide-prev");
  var next = root.querySelector(".slide-next");
  var index = 0;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function show(nextIndex) {
    index = (nextIndex + slides.length) % slides.length;
    var slide = slides[index];
    img.alt = slide.alt;
    if (img.getAttribute("src") !== slide.src) img.setAttribute("src", slide.src);
    link.setAttribute("href", slide.href);
    caption.textContent = slide.caption;
    caption.setAttribute("href", slide.href);
    count.textContent = (index + 1) + " / " + slides.length;
  }

  prev.addEventListener("click", function () { show(index - 1); });
  next.addEventListener("click", function () { show(index + 1); });

  root.addEventListener("keydown", function (event) {
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      show(index - 1);
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      show(index + 1);
    }
  });

  var startX = 0;
  var startY = 0;
  frame.addEventListener("touchstart", function (event) {
    var touch = event.changedTouches[0];
    startX = touch.clientX;
    startY = touch.clientY;
  }, { passive: true });
  frame.addEventListener("touchend", function (event) {
    var touch = event.changedTouches[0];
    var dx = touch.clientX - startX;
    var dy = touch.clientY - startY;
    if (Math.abs(dx) < 40 || Math.abs(dx) < Math.abs(dy)) return;
    show(index + (dx < 0 ? 1 : -1));
  }, { passive: true });

  if (!reduce) img.style.transition = "opacity 160ms ease";
  show(0);
})();
