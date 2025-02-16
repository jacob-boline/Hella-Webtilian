$(() => {

    $("span.inline-block.banner").hide();

    let viewportHeight = $(window).height();

    $(window).resize(function () {
        viewportHeight = $(window).height();
    });

    let scrolled = false;
    let buffer = 76;
    let index = 0;

    const trigger = 76;

    $(document).on("scroll", function () {

        let loadingHeader = $('#header-end').css('display') === 'none';
        let header = document.getElementById("page-header");

        if (loadingHeader) {

            let sticky = header.offsetTop;

            if (window.scrollY > sticky - 400) {
                header.classList.add("sticky");
            } else {
                //$('#page-header').slideUp(500);
                // $('#page-header').removeClass("sticky", 1500);
                // header.classList.remove("sticky");
            }

            if (!scrolled) {
                scrolled = true;
                let toTop = $(window).scrollTop();
                toTop = Math.round(toTop);
                let quotient = Math.floor(toTop / trigger);

                if ((toTop >= trigger) && (quotient > index)) {
                    index = buffer / trigger;
                    $(`span.inline-block.banner:nth-child(${index})`)
                        .addClass('burn')
                        .fadeIn(1000)
                        .removeClass("hidden");
                    buffer += trigger;
                }
                scrolled = false;
                return scrolled;
            }
            scrolled = false;
            return scrolled;
        } else {
            $('#page-header').addClass("unstick");
        }
    });

    //$(".inline-block.banner:first-child").css("animation", "blinker 1s step-start infinite");

});