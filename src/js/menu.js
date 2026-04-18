// ============================================
// SISTEMA DE MENÚ
// ============================================

const Menu = {
    // Elementos del DOM
    mainMenu: null,
    rankingsMenu: null,
    gameScene: null,
    gameOverScreen: null,
    introScreen: null,
    playerNameModal: null,
    selectedMap: null,
    playerName: '',
    
    // Inicializar menú
    init: function() {
        this.mainMenu = document.getElementById('mainMenu');
        this.rankingsMenu = document.getElementById('rankingsMenu');
        this.gameScene = document.getElementById('gameScene');
        this.gameOverScreen = document.getElementById('gameOverScreen');
        this.introScreen = document.getElementById('introScreen');
        this.playerNameModal = document.getElementById('playerNameModal');
        
        this.attachEventListeners();
        this.showMainMenu();
    },
    
    // Agregar listeners de eventos
    attachEventListeners: function() {
        document.getElementById('playBtn').addEventListener('click', () => this.showPlayerNameModal());
        document.getElementById('rankingsBtn').addEventListener('click', () => this.showRankings());
        document.getElementById('exitBtn').addEventListener('click', () => this.exitGame());
        document.getElementById('backFromRankingsBtn').addEventListener('click', () => this.showMainMenu());
        document.getElementById('clearRankingsBtn').addEventListener('click', () => this.clearRankingsConfirm());
        document.getElementById('backToMenuBtn').addEventListener('click', () => this.backToMenuFromGameOver());
        
        // Listeners para el modal de nombre del jugador
        document.getElementById('confirmNameBtn').addEventListener('click', () => this.confirmPlayerName());
        document.getElementById('cancelNameBtn').addEventListener('click', () => this.cancelPlayerName());
        document.getElementById('playerNameInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.confirmPlayerName();
        });
    },
    
    // Mostrar modal para nombre del jugador
    showPlayerNameModal: function() {
        this.hideAll();
        this.playerNameModal.classList.remove('hidden');
        document.getElementById('playerNameInput').value = '';
        document.getElementById('playerNameInput').focus();
    },
    
    // Confirmar nombre del jugador
    confirmPlayerName: function() {
        const nameInput = document.getElementById('playerNameInput');
        const playerName = nameInput.value.trim();
        
        if (!playerName || playerName.length === 0) {
            alert('Please enter your name');
            return;
        }
        
        this.playerName = playerName;
        this.startGame();
    },
    
    // Cancelar nombre del jugador
    cancelPlayerName: function() {
        this.playerName = '';
        this.showMainMenu();
    },
    
    // Mostrar menú principal
    showMainMenu: function() {
        this.hideAll();
        this.mainMenu.classList.remove('hidden');
        this.selectedMap = null;
    },
    
    // Mostrar rankings
    showRankings: function() {
        this.hideAll();
        this.rankingsMenu.classList.remove('hidden');
        this.populateRankings();
    },
    
    // Poblar tabla de rankings
    populateRankings: function() {
        const tbody = document.getElementById('rankingsTableBody');
        tbody.innerHTML = '';
        
        const rankings = Storage.getTopRankings();
        
        if (rankings.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="no-rankings">No scores yet</td></tr>';
            return;
        }
        
        rankings.forEach((rank, index) => {
            const row = document.createElement('tr');
            const mapName = Config.maps[rank.mapIndex] ? Config.maps[rank.mapIndex].name : 'Unknown';
            row.innerHTML = `
                <td>${index + 1}</td>
                <td>${rank.playerName}</td>
                <td>${rank.score}</td>
                <td>${mapName}</td>
                <td>${rank.round}</td>
            `;
            tbody.appendChild(row);
        });
    },
    
    // Iniciar juego
    startGame: function() {
        this.hideAll();
        this.gameScene.classList.remove('hidden');
        
        // El soundtrack global ya está sonando
        // Detener otros audios de juego si es necesario
        if (globalSoundtrack && globalSoundtrack.paused) {
            globalSoundtrack.play();
        }
        
        Game.startNewGame();
    },
    
    // Mostrar pantalla de Game Over
    showGameOver: function(finalScore, finalRound, mapIndex = 0) {
        this.hideAll();
        this.gameOverScreen.classList.remove('hidden');
        
        document.getElementById('finalScore').textContent = finalScore;
        document.getElementById('finalRound').textContent = finalRound;
        
        // Guardar puntuación con nombre y mapa final
        Storage.saveScore(finalScore, finalRound, this.playerName, mapIndex);
    },
    
    // Volver al menú desde Game Over
    backToMenuFromGameOver: function() {
        Game.stopGame();
        this.showMainMenu();
    },
    
    // Salir del juego
    exitGame: function() {
        window.close();
        // Si window.close() no funciona, simplemente mostrar un mensaje
        alert('Gracias por jugar Duck Hunt');
    },
    
    // Borrar rankings con confirmación
    clearRankingsConfirm: function() {
        if (confirm('¿Estás seguro de que deseas borrar todos los rankings? Esta acción no se puede deshacer.')) {
            Storage.clearRankings();
            this.populateRankings();
            alert('Rankings borrados exitosamente');
        }
    },
    
    // Ocultar todos los menús y pantallas
    hideAll: function() {
        this.mainMenu.classList.add('hidden');
        this.rankingsMenu.classList.add('hidden');
        this.gameScene.classList.add('hidden');
        this.gameOverScreen.classList.add('hidden');
        this.introScreen.classList.add('hidden');
        this.playerNameModal.classList.add('hidden');
    }
};
