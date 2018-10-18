ko.components.register('account-detail-popup', {
    viewModel: function(params){return new AccountDetailPopup(params)},
    template: {element: 'account-detail-popup-template'}
});


ko.components.register('account-contact-us-about', {
    viewModel: function(params){return new AccountContactUsAbout(params)},
    template: {element: 'account_contact_us_about_template'}
});
