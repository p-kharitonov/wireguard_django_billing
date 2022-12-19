if (window.$ === undefined) {
    window.$ = django.jQuery;
}

$(function () {
    let qrcode = new QRCode("qrcode", {correctLevel: QRCode.CorrectLevel.L});
    let config = $('#config').val();
    qrcode.makeCode(config);
    $('.copy-to-clipboard').on('click', function () {
      let target = $(this).data('target');
      $(target).select();
      document.execCommand('copy');
    });
});
