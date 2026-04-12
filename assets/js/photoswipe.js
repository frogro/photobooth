// patched photoswipe.js snippet
// ONLY relevant change: prevent double trigger

onClick: async (event, el, pswp) => {
    event.preventDefault();
    event.stopPropagation();

    if (photoboothTools.isPrinting) {
        return;
    }
    photoboothTools.isPrinting = true;

    const img = pswp.currSlide.data.src.split('\\').pop().split('/').pop();

    const copies = config.print.max_multi === 1 ? 1 : await photoboothTools.askCopies();

    if (!(copies && !isNaN(copies))) {
        photoboothTools.isPrinting = false;
        return;
    }

    if (config.payments.enabled) {
        photoboothTools.printPayment(img, copies, () => {
            if (typeof remoteBuzzerClient !== 'undefined') {
                remoteBuzzerClient.inProgress(false);
            }
        });
    } else {
        photoboothTools.printImage(img, copies, () => {
            if (typeof remoteBuzzerClient !== 'undefined') {
                remoteBuzzerClient.inProgress(false);
            }
        });
    }
}
