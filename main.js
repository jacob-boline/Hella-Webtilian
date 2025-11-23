import { initAboutCarousel } from "./static/hr_about/js/carousel";
import { initAboutQuotes } from "./static/hr_about/js/quotes";

document.addEventListener("DOMContentLoaded", () => {
    initAboutCarousel(document);
    initAboutQuotes(document);
});

document.addEventListener("htmx:afterSwap", event => {
    if (event.target.id === "about-carousel-container") {
        initAboutCarousel(event.target);
    }
    if (event.target.id === "about-quotes-container") {
        initAboutQuotes(event.target);
    }
});
