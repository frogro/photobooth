// patched core.js snippet
// ONLY relevant change: prevent double trigger

buttonPrint.off('click').on('click', async (event) => {
    event.preventDefault();
    event.stopPropagation();

    if (photoboothTools.isPrinting) {
        return;
    }
    photoboothTools.isPrinting = true;

    const copies = config.print.max_multi === 1 ? 1 : await photoboothTools.askCopies();

    if (!(copies && !isNaN(copies))) {
        photoboothTools.isPrinting = false;
        return;
    }

    if (config.payments.enabled) {
        photoboothTools.printPayment(filename, copies, () => {
            remoteBuzzerClient.inProgress(false);
            buttonPrint.trigger('blur');
        });
    } else {
        photoboothTools.printImage(filename, copies, () => {
            remoteBuzzerClient.inProgress(false);
            buttonPrint.trigger('blur');
        });
    }
});
