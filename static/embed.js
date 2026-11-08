(() => {
  const form = document.querySelector('#alert-form');
  if (!form) return;
  const button = document.querySelector('#submit-button');
  const emailInput = document.querySelector('#email');
  const skuInput = document.querySelector('#sku');
  const error = document.querySelector('#form-error');
  const content = document.querySelector('#form-panel');
  const success = document.querySelector('#success-panel');
  const successMsg = document.querySelector('#success-msg');
  const retry = document.querySelector('#new-alert');
  
  const showError = text => {
    error.textContent = text;
    error.hidden = false;
  };
  
  form.addEventListener('submit', async event => {
    event.preventDefault();
    error.hidden = true;
    const email = emailInput.value.trim();
    const sku = skuInput.value.trim().toUpperCase();
    
    if (!emailInput.validity.valid || !email || !sku) {
      showError('Please enter a valid email address and product SKU.');
      return;
    }
    
    button.disabled = true;
    const original = button.innerHTML;
    button.textContent = 'Registering alert…';
    
    try {
      const response = await fetch('/api/requests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, sku })
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'Could not save this alert.');
      
      content.hidden = true;
      success.hidden = false;
      if (successMsg) {
        if (result.duplicate) {
          successMsg.textContent = "You are already active on the notification list for this SKU. We'll email you the moment stock is verified!";
        } else {
          successMsg.textContent = "We've locked in your request. You will receive a notification email as soon as this item is back in stock.";
        }
      }
      window.parent?.postMessage({ type: 'restock:subscribed', sku, duplicate: !!result.duplicate }, '*');
    } catch (exc) {
      showError(exc.message || 'Something went wrong. Please try again.');
    } finally {
      button.disabled = false;
      button.innerHTML = original;
    }
  });
  
  retry?.addEventListener('click', () => {
    form.reset();
    success.hidden = true;
    content.hidden = false;
    error.hidden = true;
    const s = document.querySelector('#sku');
    if (s) s.focus();
  });
})();
