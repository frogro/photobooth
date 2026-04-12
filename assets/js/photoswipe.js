// FIXED photoswipe.js (only relevant part patched)

onClick: async (event, el, pswp) => {
    event.preventDefault();
    event.stopPropagation();

    if (photoboothTools.isPrinting) {
        return;
    }

    const img = pswp.currSlide.data.src.split(/[\\/]/).pop();

    const copies = config.print.max_multi === 1 ? 1 : await photoboothTools.askCopies();

    if (!(copies && !isNaN(copies))) {
        return;
    }

    if (config.payments.enabled) {
        photoboothTools.printPayment(img, copies, () => {
            if (typeof remoteBuzzerClient !== 'undefined') {
                remoteBuzzerClient.inProgress(false);
            }
        });
    } else {
        photoboothTools.isPrinting = true;
        photoboothTools.printImage(img, copies, () => {
            photoboothTools.isPrinting = false;
            if (typeof remoteBuzzerClient !== 'undefined') {
                remoteBuzzerClient.inProgress(false);
            }
        });
    }
};
