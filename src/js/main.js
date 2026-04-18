// ============================================
// ARCHIVO PRINCIPAL - INICIALIZACIÓN
// ============================================

// Audio global para soundtrack
let globalSoundtrack = null;
let audioStarted = false;

function initGlobalSoundtrack() {
    if (!globalSoundtrack) {
        globalSoundtrack = document.getElementById('bgAudio');
        if (globalSoundtrack) {
            globalSoundtrack.volume = 0.5;
        }
    }
}

function playAudioImmediately() {
    console.log('🎵 Intentando reproducir audio...');
    
    if (!globalSoundtrack) {
        initGlobalSoundtrack();
    }
    
    if (!audioStarted && globalSoundtrack) {
        // Remover muted para que se escuche
        globalSoundtrack.muted = false;
        
        // Intentar reproducir
        const playPromise = globalSoundtrack.play();
        
        if (playPromise !== undefined) {
            playPromise.then(() => {
                audioStarted = true;
                console.log('✅ Audio reproduciendo exitosamente');
            }).catch(error => {
                console.log('⚠️ Autoplay bloqueado por navegador:', error.message);
                // Agregar listener para reproducir en el primer click o movimiento del mouse
                setupAudioTriggers();
            });
        }
    }
}

function setupAudioTriggers() {
    console.log('📌 Escuchando por interacción del usuario para iniciar audio...');
    
    function tryPlayAudio() {
        if (!audioStarted && globalSoundtrack) {
            globalSoundtrack.muted = false;
            globalSoundtrack.play().then(() => {
                audioStarted = true;
                console.log('✅ Audio iniciado por interacción del usuario');
                // Remover listeners
                document.removeEventListener('click', tryPlayAudio);
                document.removeEventListener('mousemove', tryPlayAudio);
                document.removeEventListener('touchstart', tryPlayAudio);
                document.removeEventListener('keydown', tryPlayAudio);
            }).catch(err => console.log('Error:', err));
        }
    }
    
    // Múltiples formas de activar (click, mouse, touch, keyboard)
    document.addEventListener('click', tryPlayAudio, { once: false });
    document.addEventListener('mousemove', tryPlayAudio, { once: false });
    document.addEventListener('touchstart', tryPlayAudio, { once: false });
    document.addEventListener('keydown', tryPlayAudio, { once: false });
}

function showIntro() {
    const introScreen = document.getElementById('introScreen');
    
    // Asegurar que la intro es visible
    introScreen.classList.remove('hidden');
    introScreen.classList.remove('fade-out');
    
    // Inicializar el soundtrack
    initGlobalSoundtrack();
    
    // Intentar reproducir inmediatamente
    playAudioImmediately();
    
    // Esperar 5 segundos
    setTimeout(() => {
        // Hacer fade out de la intro
        introScreen.classList.add('fade-out');
        
        // Después del fade out, mostrar el menú
        setTimeout(() => {
            introScreen.classList.add('hidden');
            Menu.init();
        }, 500); // Tiempo del fade out animation
    }, 5000); // 5 segundos de intro
}

// Escuchar cuando el documento esté listo
window.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM Cargado - Inicializando...');
    
    // Inicializar el soundtrack
    initGlobalSoundtrack();
    
    // Mostrar la intro después de un pequeño delay
    setTimeout(() => {
        showIntro();
    }, 100);
});

// También intentar reproducir cuando la página esté completamente cargada
window.addEventListener('load', function() {
    console.log('🎬 Página completamente cargada');
    
    // Si el audio aún no ha empezado, intentar de nuevo
    if (!audioStarted) {
        console.log('🔄 Reintentando reproducción de audio...');
        playAudioImmediately();
    }
});
