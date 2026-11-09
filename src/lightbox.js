(function () {
  var buttons = Array.prototype.slice.call(document.querySelectorAll("button.zoom"));
  if (!buttons.length) return;

  var dialog = document.createElement("div");
  dialog.className = "lightbox";
  dialog.setAttribute("role", "dialog");
  dialog.setAttribute("aria-modal", "true");
  dialog.setAttribute("aria-label", "Enlarged photo");
  dialog.hidden = true;

  var img = document.createElement("img");
  img.className = "lightbox-img";
  img.alt = "";

  function control(className, label, glyph) {
    var button = document.createElement("button");
    button.type = "button";
    button.className = className;
    button.setAttribute("aria-label", label);
    var mark = document.createElement("span");
    mark.setAttribute("aria-hidden", "true");
    mark.textContent = glyph;
    button.appendChild(mark);
    return button;
  }

  var closeBtn = control("lightbox-close", "Close", "\u00d7");
  var prevBtn = control("lightbox-prev", "Previous photo", "\u2039");
  var nextBtn = control("lightbox-next", "Next photo", "\u203a");
  var many = buttons.length > 1;
  if (!many) {
    prevBtn.hidden = true;
    nextBtn.hidden = true;
  }

  dialog.appendChild(img);
  dialog.appendChild(closeBtn);
  dialog.appendChild(prevBtn);
  dialog.appendChild(nextBtn);
  document.body.appendChild(dialog);

  var index = 0;
  var opener = null;

  function fullSrc(button) {
    return button.getAttribute("data-full") || "";
  }

  function photoAlt(button) {
    var photo = button.querySelector("img");
    return photo ? photo.alt : "";
  }

  function show(nextIndex) {
    index = (nextIndex + buttons.length) % buttons.length;
    var button = buttons[index];
    var alt = photoAlt(button);
    img.alt = alt;
    img.src = fullSrc(button);
    dialog.setAttribute("aria-label", alt || "Enlarged photo");
  }

  function tabbables() {
    return [closeBtn, prevBtn, nextBtn].filter(function (el) {
      return !el.hidden;
    });
  }

  function lockScroll() {
    var gap = window.innerWidth - document.documentElement.clientWidth;
    document.documentElement.classList.add("lightbox-open");
    document.body.classList.add("lightbox-open");
    document.body.style.paddingRight = gap > 0 ? gap + "px" : "";
  }

  function unlockScroll() {
    document.documentElement.classList.remove("lightbox-open");
    document.body.classList.remove("lightbox-open");
    document.body.style.paddingRight = "";
  }

  function setPageInert(on) {
    Array.prototype.forEach.call(document.body.children, function (el) {
      if (el !== dialog) el.inert = on;
    });
  }

  function openAt(start) {
    opener = buttons[start];
    show(start);
    lockScroll();
    setPageInert(true);
    dialog.hidden = false;
    closeBtn.focus();
  }

  function close() {
    if (dialog.hidden) return;
    dialog.hidden = true;
    img.removeAttribute("src");
    img.alt = "";
    setPageInert(false);
    unlockScroll();
    if (opener && opener.focus) opener.focus();
  }

  buttons.forEach(function (button, buttonIndex) {
    button.addEventListener("click", function () {
      openAt(buttonIndex);
    });
  });

  closeBtn.addEventListener("click", close);
  prevBtn.addEventListener("click", function () {
    show(index - 1);
  });
  nextBtn.addEventListener("click", function () {
    show(index + 1);
  });

  dialog.addEventListener("click", function (event) {
    if (event.target === dialog) close();
  });

  document.addEventListener("keydown", function (event) {
    if (dialog.hidden) return;
    if (event.key === "Escape") {
      event.preventDefault();
      close();
      return;
    }
    if (many && event.key === "ArrowLeft") {
      event.preventDefault();
      show(index - 1);
      return;
    }
    if (many && event.key === "ArrowRight") {
      event.preventDefault();
      show(index + 1);
      return;
    }
    if (event.key !== "Tab") return;
    var items = tabbables();
    if (!items.length) return;
    var first = items[0];
    var last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });
})();
