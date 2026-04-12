// FIXED core.js (only relevant part patched)
// NOTE: Only guard, NO isPrinting=true before payment

buttonPrint.off('click').on('click', async (event) => {
    event.preventDefault();
    event.stopPropagation();

    if (photoboothTools.isPrinting) {
        return;
    }

    const copies = config.print.max_multi === 1 ? 1 : await photoboothTools.askCopies();

    if (!(copies && !isNaN(copies))) {
        return;
    }

    if (config.payments.enabled) {
        photoboothTools.printPayment(filename, copies, () => {
            remoteBuzzerClient.inProgress(false);
            buttonPrint.trigger('blur');
        });
    } else {
        photoboothTools.isPrinting = true;
        photoboothTools.printImage(filename, copies, () => {
            photoboothTools.isPrinting = false;
            remoteBuzzerClient.inProgress(false);
            buttonPrint.trigger('blur');
        });
    }
});
