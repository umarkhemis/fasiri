/* Fasiri docs — extra JavaScript */

document.addEventListener("DOMContentLoaded", function () {
  // Add copy feedback to install command blocks
  document.querySelectorAll("pre code").forEach(function (block) {
    if (block.textContent.startsWith("pip install")) {
      block.parentElement.setAttribute("data-copyable", "true");
    }
  });
});
