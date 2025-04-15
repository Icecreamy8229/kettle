let timeout = null;

function returnResults(user_query) {
    const resultsContainer = document.getElementById('results-container');
    console.log(user_query);
    console.log(resultsContainer);

    if (user_query.trim() === "") {
        resultsContainer.innerHTML = "";
        return;
    }

    fetch(`/search-results?search=${user_query}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.length > 0) {
            resultsContainer.innerHTML = data.map(game => {
                return `
                    <a href="/game?id=${game.game_id}" class="hitbox">
                        <div class="content">
                            <img src="../game_media/${game.game_id}/images/cover.png" alt="Game Image" class="gameImage">
                            <div class="text-container">
                                <h3>${game.game_title}</h3>
                            </div>
                            <p class="price">${game.game_price} points</p>
                        </div>
                    </a>
                `;
            }).join('');
        } else {
            resultsContainer.innerHTML = "<p>No games found.</p>";
        }
    })
}

function clearSearch() {
    const searchInput = document.getElementById('searchInput');
    searchInput.value = '';
    document.getElementById('results-container').innerHTML = '';

    const homeUrl = document.getElementById('home-url').getAttribute('data-url');
    window.location.href = homeUrl;
}

const searchBar = document.getElementById('searchInput');
searchBar.addEventListener('input', function() {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
        returnResults(searchBar.value);
    }, 1000);
});
