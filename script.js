// Add this function to handle favorite toggling
async function toggleFavorite(movieTitle, buttonElement) {
    try {
        const response = await fetch('/add_favorite', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `movie=${encodeURIComponent(movieTitle)}`
        });

        const result = await response.json();

        if (result.status === 'success') {
            buttonElement.classList.toggle('active');
            // Show a small notification
            showNotification('Favorite updated!');
        } else {
            console.error('Error:', result.message);
            showNotification(result.message, 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Failed to update favorite', 'error');
    }
}

// Add this function to check initial favorite status
async function checkFavorites() {
    try {
        const response = await fetch('/profile');
        const text = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(text, 'text/html');

        const favorites = Array.from(doc.querySelectorAll('.favorites .movie-title'))
            .map(el => el.textContent.trim());

        document.querySelectorAll('.favorite-button').forEach(button => {
            const movieTitle = button.getAttribute('data-movie');
            if (favorites.includes(movieTitle)) {
                button.classList.add('active');
            }
        });
    } catch (error) {
        console.error('Error checking favorites:', error);
    }
}

// Notification function
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 500);
    }, 3000);
}