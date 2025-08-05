// static/js/main.js
document.addEventListener('DOMContentLoaded', () => {
    const updateTokenCounter = async () => {
        const response = await fetch('/api/user/tokens/');
        const data = await response.json();
        document.getElementById('token-counter').textContent = data.remaining_tokens;
    };
    
    // Update every 30 seconds
    setInterval(updateTokenCounter, 30000);
});