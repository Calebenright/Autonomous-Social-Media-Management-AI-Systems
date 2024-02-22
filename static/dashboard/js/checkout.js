document.addEventListener('DOMContentLoaded', function () {
    var logoSwitch = document.getElementById('logo_switch');

    var prices = {
        standard: { monthly: 19, annual: 192 },
        premium: { monthly: 26, annual: 240 },
        agency: { monthly: 119, annual: 1308 }
    };

    // Function to calculate and update prices
    function updatePrices() {
        var isAnnual = logoSwitch.checked;
        
        // Calculate the effective monthly cost if paid annually
        var effectiveMonthlyStandard = (prices.standard.annual / 12).toFixed(0);
        var effectiveMonthlyPremium = (prices.premium.annual / 12).toFixed(0);
        var effectiveMonthlyAgency = (prices.agency.annual / 12).toFixed(0);

        // Update the displayed prices based on toggle state
        document.getElementById('standard-sale-price').textContent = isAnnual ? "$" + effectiveMonthlyStandard : "$" + prices.standard.monthly;
        document.getElementById('premium-sale-price').textContent = isAnnual ? "$" + effectiveMonthlyPremium : "$" + prices.premium.monthly;
        document.getElementById('agency-sale-price').textContent = isAnnual ? "$" + effectiveMonthlyAgency : "$" + prices.agency.monthly;

        // Keep the /MO text since we're showing the effective monthly price for annual plans
        var durationText = "/MO";
        document.querySelectorAll('.pricing-duration').forEach(function(duration) {
            duration.textContent = durationText;
        });
    }

    // Initial update in case the toggle is set to annual by default
    updatePrices();

    // Listen for changes on the toggle
    logoSwitch.addEventListener('change', updatePrices);

    var stripeKey = (ENVIRONMENT === 'production') 
                    ? 'pk_live_51N3DeEAy1fGRWtyhxwVX6U0p08QZ0iZqnAKlzWpOgScJZQfMbtmQjxhYddqLrKMadth9LKxQPfJp8iGoLvQeVHoP00Fy2GlpzL' 
                    : 'pk_test_51N3DeEAy1fGRWtyhZ7ES8AlLzBVVqkCPrdzhGIapo1C5HZycH1dW2GxUR7JQU4pPEHDAaFZLQdRuRQsGLvdApkbi00OdqH2Gqp';
    var stripe = Stripe(stripeKey);

    var buttons = {
        standard: document.getElementById('checkout-standard'),
        premium: document.getElementById('checkout-premium'),
        agency: document.getElementById('checkout-agency')
    };

    Object.keys(buttons).forEach(function(plan) {
        buttons[plan].addEventListener('click', function(e) {
            e.preventDefault();
            var isAnnual = document.getElementById('logo_switch').checked; // true for annual, false for monthly
            var billingCycle = isAnnual ? 'annual' : 'monthly'; // Determine the billing cycle

            fetch('/create-checkout-session/' + plan + '/' + billingCycle + '/', {
                method: 'POST',
            })
            .then(response => response.text()) // Change to .text() to see raw response
            .then(text => {
                console.log(text); // Log raw response text
                return JSON.parse(text); // Manually parse the text to JSON
            })
            .then(function(session) {
                return stripe.redirectToCheckout({ sessionId: session.sessionId });
            })
            .catch(function(error) {
                console.error('Error:', error);
            });
        });
    });
});