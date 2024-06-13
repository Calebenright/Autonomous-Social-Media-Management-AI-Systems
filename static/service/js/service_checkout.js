document.addEventListener('DOMContentLoaded', function () {
    var amountInDollars = 5; // Set the amount in dollars
    var plan = 'unlimited_service'; // Define the plan
    var billingCycle = 'monthly'; // Define the billing cycle

    var stripeKey = 'pk_live_51N3DeEAy1fGRWtyhxwVX6U0p08QZ0iZqnAKlzWpOgScJZQfMbtmQjxhYddqLrKMadth9LKxQPfJp8iGoLvQeVHoP00Fy2GlpzL'
    var stripe = Stripe(stripeKey);

    document.getElementById('checkout-agency-user').addEventListener('click', function(e) {
        e.preventDefault();

        fetch(`/create-checkout-session/${plan}/${billingCycle}/`, {
            method: 'POST',
        })
        .then(response => response.json())
        .then(session => stripe.redirectToCheckout({ sessionId: session.sessionId }))
        .catch(error => console.error('Error:', error));
    });
});
