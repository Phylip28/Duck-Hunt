// ============================================
// CONFIGURACIÓN DEL JUEGO
// ============================================

const Config = {
    // Dimensiones del juego
    gameWidth: window.innerWidth,
    gameHeight: window.innerHeight * 0.75,
    
    // Sprites
    duckImageNames: ["duck-left.gif", "duck-right.gif"],
    seagullImageNames: ["seagull-left.gif", "seagull-right.gif"],
    ghostImageNames: ["ghost-left.gif", "ghost-right.gif"],
    batImageNames: ["bat-left.gif", "bat-right.gif"],
    
    duckWidth: 120,
    duckHeight: 115,
    seagullWidth: 160,
    seagullHeight: 135,
    ghostWidth: 100,
    ghostHeight: 120,
    batWidth: 160,
    batHeight: 160,
    
    // Velocidades por personaje
    creatureTypes: {
        duck: { name: "duck", imageNames: "duckImageNames", width: 120, height: 115, baseSpeed: 4, movementType: "linear" },
        seagull: { name: "seagull", imageNames: "seagullImageNames", width: 160, height: 135, baseSpeed: 5, movementType: "linear" },
        ghost: { name: "ghost", imageNames: "ghostImageNames", width: 130, height: 150, baseSpeed: 3, movementType: "wave" },
        bat: { name: "bat", imageNames: "batImageNames", width: 160, height: 160, baseSpeed: 6, movementType: "zigzag" }
    },
    
    // Array de tipos de personajes disponibles (para selección aleatoria)
    availableCreatureTypes: ["duck", "seagull", "bat"],
    
    // Obtener un tipo de personaje aleatorio
    getRandomCreatureType: function() {
        const randomIndex = Math.floor(Math.random() * this.availableCreatureTypes.length);
        return this.availableCreatureTypes[randomIndex];
    },
    
    // Mecánicas de juego
    ducksPerRound: 6,
    shotsPerDuck: 3,
    
    // Puntuación
    pointsFirstShot: 3,
    pointsSecondShot: 2,
    pointsThirdShot: 1,
    roundBonusMultiplier: 10, // Ronda 1 = 10 puntos, Ronda 2 = 20, etc.
    
    // Velocidad
    initialDuckSpeed: 4,
    speedIncreasePerRound: 1.15,
    
    // Mapas disponibles
    maps: [
        { name: "DEATH VALLEY", file: "assets/images/bg-cloud.jpg" },
        { name: "PLAGUE", file: "assets/images/bg-plague.jpg" },
        { name: "DANGER ZONE", file: "assets/images/bg-nuclear.jpg" },
        { name: "HAUNTED CASTLE", file: "assets/images/bg-castle.jpg" },
        { name: "WITCH HOUSE", file: "assets/images/bg-moon.jpg" },
        { name: "GATE TO HELL", file: "assets/images/bg-volcano.jpg" },
        { name: "HELL", file: "assets/images/bg-hell.jpg" }
    ],
    
    // Array para guardar mapas aleatorios por ronda
    randomMapQueue: [],
    
    // Generar cola de 7 mapas aleatoriamente (sin repetición)
    generateRandomMapQueue: function() {
        const indices = [0, 1, 2, 3, 4, 5, 6];
        // Fisher-Yates shuffle
        for (let i = indices.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [indices[i], indices[j]] = [indices[j], indices[i]];
        }
        this.randomMapQueue = indices;
        return indices;
    },
    
    // Obtener el siguiente mapa aleatorio (circular si se agotan)
    getNextRandomMap: function(roundNumber) {
        if (this.randomMapQueue.length === 0) {
            this.generateRandomMapQueue();
        }
        const mapIndex = this.randomMapQueue.shift();
        return this.maps[mapIndex];
    },
    
    // Mapeo de rondas a mapas (cada 2 rondas cambia de mapa) - DEPRECATED, pero se mantiene por compatibilidad
    roundToMapIndex: function(round) {
        if (round <= 2) return 0;      // DEATH VALLEY
        if (round <= 4) return 1;      // PLAGUE
        if (round <= 6) return 2;      // DANGER ZONE
        if (round <= 8) return 3;      // HAUNTED CASTLE
        if (round <= 10) return 4;     // WITCH HOUSE
        if (round <= 12) return 5;     // GATE TO HELL
        return 6;                       // HELL (ronda 13+)
    },
    
    // Sonidos
    sounds: {
        duckShot: "assets/audio/duck-shot.mp3",
        duckFlap: "assets/audio/duck-flap.mp3",
        duckQuack: "assets/audio/duck-quack.mp3",
        dogScore: "assets/audio/dog-score.mp3",
        soundtrack: "assets/audio/soundtrack.mp3"
    },
    
    // Imágenes
    images: {
        background: "assets/images/duckhunt-bg-4k.jpg",
        target: "assets/images/target.png",
        dogHappyWithDuck: "assets/images/dog-duck1.png",
        dogSad: "assets/images/dog-duck2.png",
        duckLeft: "assets/images/duck-left.gif",
        duckRight: "assets/images/duck-right.gif"
    },
    
    // Rutas de fuentes
    fonts: {
        gameFont: "assets/fonts/game-font.otf"
    }
};
