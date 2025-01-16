document.addEventListener('DOMContentLoaded', function () {

    var stripeKey = 'pk_live_51N3DeEAy1fGRWtyhxwVX6U0p08QZ0iZqnAKlzWpOgScJZQfMbtmQjxhYddqLrKMadth9LKxQPfJp8iGoLvQeVHoP00Fy2GlpzL'
    var stripe = Stripe(stripeKey);

    // document.getElementById('checkout-1').addEventListener('click', function(e) {
    //     e.preventDefault();

    //     fetch(`/create-checkout-session/10_DOLLAR_MONTHLY_PRICE_ID/`, {
    //         method: 'POST',
    //     })
    //     .then(response => response.json())
    //     .then(session => stripe.redirectToCheckout({ sessionId: session.sessionId }))
    //     .catch(error => console.error('Error:', error));
    // });

    document.getElementById('checkout-2').addEventListener('click', function(e) {
        e.preventDefault();

        fetch(`/create-checkout-session/30_DOLLAR_MONTHLY_PRICE_ID/`, {
            method: 'POST',
        })
        .then(response => response.json())
        .then(session => stripe.redirectToCheckout({ sessionId: session.sessionId }))
        .catch(error => console.error('Error:', error));
    });
});
