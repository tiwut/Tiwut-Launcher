document.addEventListener('DOMContentLoaded', () => {
    fetchAndDisplayApps();
});

async function fetchAndDisplayApps() {
    const appGrid = document.getElementById('app-grid');

    try {
        const response = await fetch('library.tiwut');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const textData = await response.text();
        const apps = parseLibrary(textData);

        // Lade-Spinner entfernen
        appGrid.innerHTML = ''; 

        apps.forEach(app => {
            const card = createAppCard(app);
            appGrid.appendChild(card);
        });

    } catch (error) {
        appGrid.innerHTML = `<p style="color: #ff8a8a;">Fehler beim Laden der App-Bibliothek: ${error.message}</p>`;
    }
}

function parseLibrary(text) {
    return text.split('\n')
        .filter(line => line.trim() !== '')
        .map(line => {
            const parts = line.split(';');
            return {
                name: parts[0] || 'Unbekannte App',
                downloadUrl: parts[1] || '',
                websiteUrl: parts[2] || '',
                iconUrl: parts[3] || ''
            };
        });
}

function createAppCard(app) {
    const card = document.createElement('div');
    card.className = 'app-card';

    // App-Icon
    const icon = document.createElement('img');
    icon.className = 'app-icon';
    icon.src = app.iconUrl;
    // Fallback, wenn das Bild nicht geladen werden kann
    icon.onerror = () => { icon.style.display = 'none'; }; 
    if (!app.iconUrl) {
        icon.style.display = 'none';
    }

    // App-Name
    const title = document.createElement('h3');
    title.textContent = app.name;

    // Button-Gruppe
    const buttonGroup = document.createElement('div');
    buttonGroup.className = 'button-group';
    
    // WICHTIG: Der Link für das benutzerdefinierte Protokoll
    const installLink = document.createElement('a');
    // Wir müssen die Parameter URL-kodieren, falls sie Sonderzeichen enthalten
    const safeName = encodeURIComponent(app.name);
    const safeUrl = encodeURIComponent(app.downloadUrl);
    installLink.href = `tiwut-store://install?name=${safeName}&url=${safeUrl}`;
    installLink.className = 'btn btn-install';
    installLink.textContent = 'Installieren';

    // Website-Link
    const websiteLink = document.createElement('a');
    websiteLink.href = app.websiteUrl;
    websiteLink.target = '_blank'; // In neuem Tab öffnen
    websiteLink.className = 'btn btn-website';
    websiteLink.textContent = 'Website';
    if (!app.websiteUrl) {
        websiteLink.style.display = 'none';
    }
    
    buttonGroup.appendChild(installLink);
    buttonGroup.appendChild(websiteLink);

    card.appendChild(icon);
    card.appendChild(title);
    card.appendChild(buttonGroup);

    return card;
}