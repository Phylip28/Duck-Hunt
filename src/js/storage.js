// ============================================
// SISTEMA DE ALMACENAMIENTO DE DATOS
// ============================================

const Storage = {
    STORAGE_KEY: "duckHuntRankings",
    
    // Guardar una puntuación
    saveScore: function(score, round, playerName = 'Player', mapIndex = 0) {
        let rankings = this.getRankings();
        
        rankings.push({
            playerName: playerName,
            score: score,
            round: round,
            mapIndex: mapIndex
        });
        
        // Ordenar de mayor a menor puntuación
        rankings.sort((a, b) => b.score - a.score);
        
        // Guardar en localStorage
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(rankings));
    },
    
    // Obtener todos los rankings
    getRankings: function() {
        const data = localStorage.getItem(this.STORAGE_KEY);
        return data ? JSON.parse(data) : [];
    },
    
    // Obtener los top 10
    getTopRankings: function(limit = 10) {
        return this.getRankings().slice(0, limit);
    },
    
    // Limpiar rankings (opcional)
    clearRankings: function() {
        localStorage.removeItem(this.STORAGE_KEY);
    }
};
