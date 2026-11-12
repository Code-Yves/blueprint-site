(function () {
  var root = document.querySelector("[data-slideshow]");
  if (!root) return;
  var dataEl = document.getElementById("slide-data");
  if (!dataEl) return;
  var slides = JSON.parse(dataEl.textContent);
  if (!slides.length) return;
  var frame = root.querySelector(".slide-frame");
  var photos = root.querySelectorAll(".slide-photo");
  var link = root.querySelector(".slide-link");
  var prev = root.querySelector(".slide-prev");
  var next = root.querySelector(".slide-next");
  var index = 0;
  var front = 0;
  var token = 0;
  var timer = 0;
  var holdUntil = 0;
  var hovering = false;
  var focused = false;
  var motion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var reduce = motion.matches;

  function blocked() {
    return reduce || document.hidden || hovering || focused;
  }

  function arm() {
    window.clearTimeout(timer);
    if (blocked()) return;
    var wait = 5000;
    var remaining = holdUntil - Date.now();
    if (remaining > wait) wait = remaining;
    timer = window.setTimeout(function () {
      if (blocked() || Date.now() < holdUntil) {
        arm();
        return;
      }
      show(index + 1);
      arm();
    }, wait);
  }

  function hold() {
    holdUntil = Date.now() + 8000;
    arm();
  }

  function show(nextIndex) {
    index = (nextIndex + slides.length) % slides.length;
    var slide = slides[index];
    var current = photos[front];
    var incoming = photos[1 - front];
    var my = ++token;
    var shown = false;
    link.setAttribute("href", slide.href);
    if (current.getAttribute("src") === slide.src) {
      current.alt = slide.alt;
      return;
    }
    function reveal() {
      if (shown || my !== token) return;
      shown = true;
      incoming.alt = slide.alt;
      current.alt = "";
      incoming.removeAttribute("aria-hidden");
      current.setAttribute("aria-hidden", "true");
      incoming.classList.add("is-active");
      current.classList.remove("is-active");
      front = 1 - front;
    }
    incoming.onload = function () {
      incoming.onload = null;
      reveal();
    };
    incoming.src = slide.src;
    if (reduce || (incoming.complete && incoming.naturalWidth)) reveal();
  }

  prev.addEventListener("click", function () {
    hold();
    show(index - 1);
  });
  next.addEventListener("click", function () {
    hold();
    show(index + 1);
  });

  root.addEventListener("keydown", function (event) {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    hold();
    show(index + (event.key === "ArrowRight" ? 1 : -1));
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
    hold();
    show(index + (dx < 0 ? 1 : -1));
  }, { passive: true });

  root.addEventListener("pointerenter", function (event) {
    if (event.pointerType && event.pointerType !== "mouse") return;
    hovering = true;
    window.clearTimeout(timer);
  });
  root.addEventListener("pointerleave", function (event) {
    if (event.pointerType && event.pointerType !== "mouse") return;
    hovering = false;
    arm();
  });
  root.addEventListener("focusin", function () {
    focused = true;
    window.clearTimeout(timer);
  });
  root.addEventListener("focusout", function (event) {
    if (root.contains(event.relatedTarget)) return;
    focused = false;
    arm();
  });
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) window.clearTimeout(timer);
    else arm();
  });
  if (motion.addEventListener) {
    motion.addEventListener("change", function () {
      reduce = motion.matches;
      if (reduce) window.clearTimeout(timer);
      else arm();
    });
  }

  arm();
})();
