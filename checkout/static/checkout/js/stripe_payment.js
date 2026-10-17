/* jshint esversion: 11 */
/* global Stripe */

// Stripe Payment Element.
// Adapted from Stripe's "Accept a payment" documentation:
// https://docs.stripe.com/payments/accept-a-payment?plaform=web&ui=elements
//

document.addEventListener('DOMContentLoaded', function(){
    const publicKey = JSON.parse(document.getElementById('stripe-public-key').textContent);
    const clientSecret = JSON.parse(document.getElementById('client-secret').textContent);
    const returnUrl = JSON.parse(document.getElementById('return-url').textContent);

    const stripe = Stripe(publicKey);
    const elements = stripe.elements({
        clientSecret: clientSecret,
        appearance: { theme: 'stripe', variables: { colorPrimary: '#32174d' } },
    });
    elements.create('payment').mount('#payment-element');

    const form = document.getElementById('payment-form');
    const button = document.getElementById('submit-button');
    const errors = document.getElementById('payment-errors');

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        button.disabled = true;
        errors.textContent = '';

        const { error } = await stripe.confirmPayment({
            elements,
            confirmParams: { return_url: returnUrl },
        });

        // Only reached if the payment fails, e.g. a declined card.
        // If it succeeds, Stripe sends the browser to returnUrl instead.
        errors.textContent = error.message;
        button.disabled = false;
    });
});