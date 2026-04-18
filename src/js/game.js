// ============================================
// LÓGICA DEL JUEGO
// ============================================

const Game = {
    // Estado del juego
    currentRound: 1,
    totalScore: 0,
    remainingDucks: 0,
    ducksInRound: 0,
    shotsRemaining: Config.shotsPerDuck,
    currentDeer: null,
    duckSpeed: Config.initialDuckSpeed,
    gameActive: false,
    currentDuckIndex: 0,
    ducksCaught: 0,
    missedClickListener: null,
    shootingBlocked: false,
    currentMapIndex: 0,  // Índice del mapa actual
    currentMapName: "---",  // Nombre del mapa actual
    
    // Elementos del DOM
    gameContainer: null,
    gameHUD: {
        totalScore: null,
        roundNumber: null,
        ammoCount: null,
        ducksRemaining: null,
        mapName: null
    },
    
    // Audio
    audioElements: {},
    
    // Inicializar sonidos
    initAudio: function() {
        this.audioElements = {
            duckShot: new Audio(Config.sounds.duckShot),
            duckFlap: new Audio(Config.sounds.duckFlap),
            duckQuack: new Audio(Config.sounds.duckQuack),
            dogScore: new Audio(Config.sounds.dogScore),
            soundtrack: new Audio(Config.sounds.soundtrack)
        };
        // Configurar volumen del soundtrack
        this.audioElements.soundtrack.volume = 0.5;
    },
    
    // Cambiar mapa a uno aleatorio
    changeMapForRound: function() {
        const map = Config.getNextRandomMap(this.currentRound);
        
        // Encontrar el índice del mapa en el array de mapas
        this.currentMapIndex = Config.maps.indexOf(map);
        this.currentMapName = map.name;  // Guardar nombre del mapa
        
        if (map) {
            document.body.style.backgroundImage = `url('${map.file}')`;
            
            // Cambiar cursor según mapa
            let targetImage = 'assets/images/target.png';
            if (this.currentMapIndex === 1 || this.currentMapIndex === 2 || this.currentMapIndex === 3 || this.currentMapIndex === 5 || this.currentMapIndex === 6) {
                targetImage = 'assets/images/targeti.png';
            }
            this.gameContainer.style.cssText = `cursor: url('${targetImage}') 10 10, crosshair !important;`;
        }
    },
    
    // Inicializar el juego
    startNewGame: function() {
        this.currentRound = 1;
        this.totalScore = 0;
        this.gameActive = true;
        this.currentDuckIndex = 0;
        this.duckSpeed = Config.initialDuckSpeed;
        
        // Generar cola de 7 mapas aleatoriamente
        Config.generateRandomMapQueue();
        
        this.gameContainer = document.getElementById('gameContainer');
        this.gameContainer.innerHTML = '';
        
        // Cambiar a primer mapa aleatorio
        this.changeMapForRound();
        
        this.gameHUD.totalScore = document.getElementById('totalScore');
        this.gameHUD.roundNumber = document.getElementById('roundNumber');
        this.gameHUD.ammoCount = document.getElementById('ammoCount');
        this.gameHUD.ducksRemaining = document.getElementById('ducksRemaining');
        this.gameHUD.mapName = document.getElementById('mapName');
        
        this.initAudio();
        this.addMissClickListener();
        this.startRound();
    },
    
    // Agregar listener para clicks fallidos
    addMissClickListener: function() {
        if (this.missedClickListener) {
            this.gameContainer.removeEventListener('click', this.missedClickListener);
        }
        
        this.missedClickListener = (e) => {
            // Solo contar como fallo si el click es directamente en el contenedor
            if (e.target === this.gameContainer) {
                this.missDuck();
            }
        };
        
        this.gameContainer.addEventListener('click', this.missedClickListener);
    },
    
    // Iniciar nueva ronda
    startRound: function() {
        // Cambiar mapa aleatoriamente cada ronda
        if (this.currentRound > 1) {  // No cambiar en la primera ronda
            this.changeMapForRound();
        }
        
        this.remainingDucks = Config.ducksPerRound;
        this.currentDuckIndex = 0;
        this.ducksCaught = 0;
        this.shotsRemaining = Config.shotsPerDuck;
        
        this.updateHUD();
        
        // Esperar un poco antes de mostrar el primer personaje
        setTimeout(() => {
            if (this.gameActive) {
                this.spawnNextCreature();
            }
        }, 1500);
    },
    
    // Obtener tipo de criatura aleatoria
    getCreatureTypeForRound: function() {
        return Config.getRandomCreatureType();
    },
    
    // Generar el siguiente personaje (criatura)
    spawnNextCreature: function() {
        if (!this.gameActive) return;
        
        if (this.currentDuckIndex >= Config.ducksPerRound) {
            // Ronda completada
            this.completeRound();
            return;
        }
        
        // Obtener tipo de criatura para esta ronda
        const creatureType = this.getCreatureTypeForRound();
        const creatureConfig = Config.creatureTypes[creatureType];
        const imageNames = Config[creatureConfig.imageNames];
        const imageName = imageNames[Math.floor(Math.random() * 2)];
        
        let creatureImage = document.createElement('img');
        creatureImage.src = `assets/images/${imageName}`;
        creatureImage.width = creatureConfig.width;
        creatureImage.height = creatureConfig.height;
        creatureImage.draggable = false;
        creatureImage.style.position = 'absolute';
        
        const startX = Math.random() * (Config.gameWidth - creatureConfig.width);
        const startY = Math.random() * (Config.gameHeight * 0.6);
        
        creatureImage.style.left = startX + 'px';
        creatureImage.style.top = startY + 'px';
        
        this.gameContainer.appendChild(creatureImage);
        
        const velocityX = imageName.includes('left') ? -this.duckSpeed : this.duckSpeed;
        const velocityY = (Math.random() - 0.5) * this.duckSpeed;
        
        const creatureData = {
            element: creatureImage,
            x: startX,
            y: startY,
            velocityX: velocityX,
            velocityY: velocityY,
            imageName: imageName,
            type: creatureType,
            baseSpeed: creatureConfig.baseSpeed,
            width: creatureConfig.width,
            height: creatureConfig.height,
            movementType: creatureConfig.movementType,
            animationTime: 0  // Para movimientos complejos
        };
        
        this.currentDeer = creatureData;
        this.shotsRemaining = Config.shotsPerDuck;
        this.shootingBlocked = false;
        
        // Event listener para disparo
        creatureImage.addEventListener('click', (e) => {
            e.stopPropagation();
            this.shootDuck();
        });
        
        // Iniciar animación según tipo de movimiento
        if (creatureData.movementType === 'wave') {
            this.animateCreatureWave();
        } else if (creatureData.movementType === 'zigzag') {
            this.animateCreatureZigzag();
        } else {
            // Movimiento lineal (duck y seagull)
            this.animateDuck();
        }
        
        this.currentDuckIndex++;
        this.updateHUD();
    },
    
    // Animar personaje - movimiento lineal (patos y gaviotas)
    animateDuck: function() {
        if (!this.gameActive || !this.currentDeer) return;
        
        const gameWidth = Config.gameWidth;
        const gameHeight = Config.gameHeight;
        const creature = this.currentDeer;
        const imageNames = Config[Config.creatureTypes[creature.type].imageNames];
        
        const move = () => {
            if (!this.gameActive || !this.currentDeer || this.currentDeer !== creature) {
                return;
            }
            
            creature.x += creature.velocityX;
            creature.y += creature.velocityY;
            
            // Rebotar en los bordes
            if (creature.x < 0 || creature.x + creature.width > gameWidth) {
                creature.x = creature.x < 0 ? 0 : gameWidth - creature.width;
                creature.velocityX *= -1;
                
                if (creature.velocityX < 0) {
                    creature.element.src = `assets/images/${imageNames[0]}`;
                } else {
                    creature.element.src = `assets/images/${imageNames[1]}`;
                }
            }
            
            if (creature.y < 0 || creature.y + creature.height > gameHeight) {
                creature.y = creature.y < 0 ? 0 : gameHeight - creature.height;
                creature.velocityY *= -1;
            }
            
            creature.element.style.left = creature.x + 'px';
            creature.element.style.top = creature.y + 'px';
            
            requestAnimationFrame(move);
        };
        
        move();
    },
    
    // Animar personaje - movimiento ondulante (fantasmas)
    animateCreatureWave: function() {
        if (!this.gameActive || !this.currentDeer) return;
        
        const gameWidth = Config.gameWidth;
        const gameHeight = Config.gameHeight;
        const creature = this.currentDeer;
        const imageNames = Config[Config.creatureTypes[creature.type].imageNames];
        const waveAmplitude = 50;  // Amplitud de la onda
        const waveFrequency = 0.1; // Frecuencia de la onda
        
        const move = () => {
            if (!this.gameActive || !this.currentDeer || this.currentDeer !== creature) {
                return;
            }
            
            creature.animationTime += 1;
            
            // Movimiento horizontal
            creature.x += creature.velocityX;
            
            // Movimiento vertical ondulante
            creature.y += Math.sin(creature.animationTime * waveFrequency) * 2;
            
            // Rebotar en los bordes horizontales
            if (creature.x < 0 || creature.x + creature.width > gameWidth) {
                creature.x = creature.x < 0 ? 0 : gameWidth - creature.width;
                creature.velocityX *= -1;
                
                if (creature.velocityX < 0) {
                    creature.element.src = `assets/images/${imageNames[0]}`;
                } else {
                    creature.element.src = `assets/images/${imageNames[1]}`;
                }
            }
            
            // Limitar movimiento vertical
            if (creature.y < 0 || creature.y + creature.height > gameHeight) {
                creature.y = Math.max(0, Math.min(creature.y, gameHeight - creature.height));
            }
            
            creature.element.style.left = creature.x + 'px';
            creature.element.style.top = creature.y + 'px';
            
            requestAnimationFrame(move);
        };
        
        move();
    },
    
    // Animar personaje - movimiento en zigzag (murciélagos)
    animateCreatureZigzag: function() {
        if (!this.gameActive || !this.currentDeer) return;
        
        const gameWidth = Config.gameWidth;
        const gameHeight = Config.gameHeight;
        const creature = this.currentDeer;
        const imageNames = Config[Config.creatureTypes[creature.type].imageNames];
        const zigzagIntensity = 3;  // Intensidad del zigzag
        
        const move = () => {
            if (!this.gameActive || !this.currentDeer || this.currentDeer !== creature) {
                return;
            }
            
            creature.animationTime += 1;
            
            // Movimiento horizontal
            creature.x += creature.velocityX;
            
            // Movimiento vertical en zigzag
            if (Math.sin(creature.animationTime * 0.15) > 0) {
                creature.y -= zigzagIntensity;
            } else {
                creature.y += zigzagIntensity;
            }
            
            // Rebotar en los bordes horizontales
            if (creature.x < 0 || creature.x + creature.width > gameWidth) {
                creature.x = creature.x < 0 ? 0 : gameWidth - creature.width;
                creature.velocityX *= -1;
                
                if (creature.velocityX < 0) {
                    creature.element.src = `assets/images/${imageNames[0]}`;
                } else {
                    creature.element.src = `assets/images/${imageNames[1]}`;
                }
            }
            
            // Limitar movimiento vertical
            if (creature.y < 0 || creature.y + creature.height > gameHeight) {
                creature.y = Math.max(0, Math.min(creature.y, gameHeight - creature.height));
            }
            
            creature.element.style.left = creature.x + 'px';
            creature.element.style.top = creature.y + 'px';
            
            requestAnimationFrame(move);
        };
        
        move();
    },
    
    // Disparo a pato
    shootDuck: function() {
        if (!this.gameActive || !this.currentDeer || this.shotsRemaining <= 0 || this.shootingBlocked) return;
        
        this.shotsRemaining--;
        
        // Sonido de disparo
        this.audioElements.duckShot.currentTime = 0;
        this.audioElements.duckShot.play();
        
        // Sonido de aleteo del pato
        this.audioElements.duckFlap.currentTime = 0;
        this.audioElements.duckFlap.play();
        
        let pointsEarned = 0;
        
        if (this.shotsRemaining === 2) {
            // Primer tiro exitoso: 3 puntos
            pointsEarned = Config.pointsFirstShot;
            this.totalScore += pointsEarned;
        } else if (this.shotsRemaining === 1) {
            // Segundo tiro exitoso: 2 puntos
            pointsEarned = Config.pointsSecondShot;
            this.totalScore += pointsEarned;
        } else if (this.shotsRemaining === 0) {
            // Tercer tiro exitoso: 1 punto
            pointsEarned = Config.pointsThirdShot;
            this.totalScore += pointsEarned;
        }
        
        // Incrementar contador de patos cazados ANTES de actualizar HUD
        this.ducksCaught++;
        
        this.updateHUD();
        
        // Mostrar puntuación flotante
        this.showFloatingScore(pointsEarned, this.currentDeer);
        
        // Mostrar mancha de sangre realista en la posición del pato
        if (this.currentDeer) {
            const duckRect = this.currentDeer.element.getBoundingClientRect();
            this.showBloodSplatter(duckRect.left + duckRect.width / 2, duckRect.top + duckRect.height / 2);
        }
        
        // Mostrar animación del perro con pato
        this.showDogWithDuck();
        
        // Remover pato actual
        if (this.currentDeer && this.gameContainer.contains(this.currentDeer.element)) {
            this.gameContainer.removeChild(this.currentDeer.element);
            this.currentDeer = null;
        }
        
        // Generar siguiente criatura
        setTimeout(() => {
            if (this.gameActive) {
                this.spawnNextCreature();
            }
        }, 2000);
    },
    
    // Mostrar salpicadura de sangre realista con Canvas
    showBloodSplatter: function(x, y) {
        // Mostrar blood.png en el centro
        const bloodImage = document.createElement('img');
        bloodImage.src = 'assets/images/blood.png';
        bloodImage.style.position = 'fixed';
        bloodImage.style.left = (x - 80) + 'px';
        bloodImage.style.top = (y - 80) + 'px';
        bloodImage.style.width = '160px';
        bloodImage.style.height = '160px';
        bloodImage.style.zIndex = '350';
        bloodImage.style.pointerEvents = 'none';
        bloodImage.style.opacity = '1';
        bloodImage.draggable = false;
        
        document.body.appendChild(bloodImage);
        
        // Crear manchas blood2.png dispersas por toda la pantalla
        const splatCount = 20;
        for (let i = 0; i < splatCount; i++) {
            // Dispersar manchas en radio más amplio
            const angle = Math.random() * Math.PI * 2;
            const distance = Math.random() * 500 + 100; // Más dispersas
            const splatX = x + Math.cos(angle) * distance;
            const splatY = y + Math.sin(angle) * distance;
            
            // Crear image element para blood2.png
            const splatImage = document.createElement('img');
            splatImage.src = 'assets/images/blood2.png';
            splatImage.style.position = 'fixed';
            splatImage.style.left = (splatX - 125) + 'px';
            splatImage.style.top = (splatY - 125) + 'px';
            splatImage.style.width = '250px';
            splatImage.style.height = '250px';
            splatImage.style.zIndex = '349';
            splatImage.style.pointerEvents = 'none';
            splatImage.style.opacity = '1';
            splatImage.draggable = false;
            
            document.body.appendChild(splatImage);
            
            // Fade out de manchas blood2.png
            let splatOpacity = 1;
            const splatFadeInterval = setInterval(() => {
                splatOpacity -= 0.05;
                splatImage.style.opacity = splatOpacity;
                if (splatOpacity <= 0) {
                    clearInterval(splatFadeInterval);
                    document.body.removeChild(splatImage);
                }
            }, 80);
        }
        
        // Fade out de blood.png
        let opacity = 1;
        const fadeInterval = setInterval(() => {
            opacity -= 0.05;
            bloodImage.style.opacity = opacity;
            if (opacity <= 0) {
                clearInterval(fadeInterval);
                document.body.removeChild(bloodImage);
            }
        }, 80);
    },
    
    // Mostrar puntuación flotante
    showFloatingScore: function(points, duck) {
        const floatingScore = document.createElement('div');
        floatingScore.className = 'floating-score';
        floatingScore.textContent = `+${points}`;
        
        // Posicionar en el centro del pato
        const duckRect = duck.element.getBoundingClientRect();
        floatingScore.style.left = (duckRect.left + duckRect.width / 2 - 24) + 'px';
        floatingScore.style.top = duckRect.top + 'px';
        
        document.body.appendChild(floatingScore);
        
        // Remover después de la animación
        setTimeout(() => {
            if (document.body.contains(floatingScore)) {
                document.body.removeChild(floatingScore);
            }
        }, 1500);
    },
    
    // Fallo - tres tiros perdidos
    missDuck: function() {
        if (!this.gameActive || !this.currentDeer || this.shootingBlocked) return;
        
        // Sonido - sin sonido específico, solo se usa el del disparo
        this.audioElements.duckShot.currentTime = 0;
        this.audioElements.duckShot.play();
        
        this.shotsRemaining--;
        this.updateHUD();
        
        if (this.shotsRemaining <= 0) {
            // Game Over
            this.gameOver();
        }
    },
    
    // Mostrar perro con pato
    showDogWithDuck: function() {
        this.shootingBlocked = true;
        
        // Sonido
        this.audioElements.dogScore.currentTime = 0;
        this.audioElements.dogScore.play();
        
        setTimeout(() => {
            this.shootingBlocked = false;
        }, 1500);
    },
    
    // Mostrar perro triste (Game Over)
    showSadDog: function() {
        const dogImage = document.createElement('img');
        dogImage.src = 'assets/images/dog-duck2.png';
        dogImage.width = 920;
        dogImage.height = 690;
        dogImage.style.position = 'fixed';
        dogImage.style.bottom = '0px';
        dogImage.style.left = '50%';
        dogImage.style.transform = 'translateX(-50%)';
        dogImage.style.zIndex = '1000';
        dogImage.draggable = false;
        
        this.gameContainer.appendChild(dogImage);
        
        // Sonido de cuack cuando el juego termina
        this.audioElements.duckQuack.currentTime = 0;
        this.audioElements.duckQuack.play();
        
        return dogImage;
    },
    
    // Ronda completada
    completeRound: function() {
        const roundBonus = this.currentRound * Config.roundBonusMultiplier;
        this.totalScore += roundBonus;
        
        this.currentRound++;
        this.duckSpeed += Config.speedIncreasePerRound;
        
        this.updateHUD();
        
        // Mostrar perro con pato antes de siguiente ronda
        this.showDogWithDuck();
        
        // Mostrar bonificación de ronda
        this.showRoundBonus(roundBonus);
        
        setTimeout(() => {
            if (this.gameActive) {
                this.startRound();
            }
        }, 3000);
    },
    
    // Mostrar bonificación de ronda
    showRoundBonus: function(bonus) {
        this.shootingBlocked = true;
        
        const bonusContainer = document.createElement('div');
        bonusContainer.className = 'round-bonus';
        
        bonusContainer.innerHTML = `
            <div class="round-bonus-title">¡ROUND COMPLETED!</div>
            <div class="round-bonus-text">Bonus:</div>
            <div class="round-bonus-points">+${bonus}</div>
        `;
        
        document.body.appendChild(bonusContainer);
        
        // Remover después de que se vea
        setTimeout(() => {
            if (document.body.contains(bonusContainer)) {
                document.body.removeChild(bonusContainer);
            }
            this.shootingBlocked = false;
        }, 3000);
    },
    
    // Game Over
    gameOver: function() {
        this.gameActive = false;
        
        // Remover pato si existe
        if (this.currentDeer && this.gameContainer.contains(this.currentDeer.element)) {
            this.gameContainer.removeChild(this.currentDeer.element);
        }
        
        this.currentDeer = null;
        
        // Mostrar perro triste
        this.showSadDog();
        
        // Mostrar pantalla de Game Over
        setTimeout(() => {
            Menu.showGameOver(this.totalScore, this.currentRound, this.currentMapIndex);
        }, 2500);
    },
    
    // Actualizar HUD
    updateHUD: function() {
        this.gameHUD.totalScore.textContent = this.totalScore;
        this.gameHUD.roundNumber.textContent = this.currentRound;
        this.gameHUD.mapName.textContent = this.currentMapName;
        
        // Actualizar puntos de munición
        const ammoDots = this.gameHUD.ammoCount.querySelectorAll('.ammo-dot');
        ammoDots.forEach((dot, index) => {
            // Si el índice es mayor al número de disparos restantes, está vacío (blanco)
            if (index >= this.shotsRemaining) {
                dot.classList.remove('red');
                dot.classList.add('white');
            } else {
                dot.classList.remove('white');
                dot.classList.add('red');
            }
        });
        
        // Actualizar cantidad de patos cazados (cazados/total)
        const ducksCaughtElement = document.getElementById('ducksCaught');
        if (ducksCaughtElement) {
            ducksCaughtElement.textContent = this.ducksCaught;
        }
    },
    
    // Detener juego
    stopGame: function() {
        this.gameActive = false;
        
        // Remover listener de clicks fallidos
        if (this.missedClickListener && this.gameContainer) {
            this.gameContainer.removeEventListener('click', this.missedClickListener);
        }
        
        if (this.currentDeer && this.gameContainer && this.gameContainer.contains(this.currentDeer.element)) {
            try {
                this.gameContainer.removeChild(this.currentDeer.element);
            } catch (e) {
                // Ya fue removido
            }
        }
        this.gameContainer.innerHTML = '';
    }
};
