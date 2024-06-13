document.addEventListener('DOMContentLoaded', function () {
    var amountInDollars = 3; // Set the amount in dollars
    var plan = 'agency_user'; // Define the plan
    var billingCycle = 'monthly'; // Define the billing cycle

    var stripeKey = (ENVIRONMENT === 'production') 
                    ? 'pk_live_51N3DeEAy1fGRWtyhxwVX6U0p08QZ0iZqnAKlzWpOgScJZQfMbtmQjxhYddqLrKMadth9LKxQPfJp8iGoLvQeVHoP00Fy2GlpzL' 
                    : 'pk_test_51N3DeEAy1fGRWtyhZ7ES8AlLzBVVqkCPrdzhGIapo1C5HZycH1dW2GxUR7JQU4pPEHDAaFZLQdRuRQsGLvdApkbi00OdqH2Gqp';
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
