"""
Generador de Números Pseudoaleatorios (PRNG) - Método de Congruencias Lineales
================================================================================

Implementación de un Generador de Números Pseudoaleatorios (PRNG) basado en
el Método Congruencial Lineal (LCG), sin dependencia de librerías nativas
de aleatoriedad como `random`.

Fórmula Matemática (LCG):
    X_(n+1) = (a * X_n + c) mod m

Donde:
    - X_n: Estado actual (semilla)
    - a: Multiplicador = 1103515245 (parámetro estándar de glibc)
    - c: Incremento = 12345 (parámetro estándar de glibc)
    - m: Módulo = 2^32 = 4294967296 (rango máximo de 32 bits sin signo)
    - X_(n+1): Siguiente número pseudoaleatorio

Referencias:
    - Parámetros validados según estándar POSIX/glibc
    - Período completo: 2^32
    - Ideal para videojuegos y simulaciones
    - Determinista: reproducible con misma semilla
"""

from __future__ import annotations


class LCG:
    """
    Generador Lineal Congruencial (LCG) de Números Pseudoaleatorios.
    
    Utiliza la fórmula: X_(n+1) = (a * X_n + c) mod m
    Con parámetros estándar de glibc para máxima compatibilidad.
    """
    
    # Parámetros de la fórmula LCG (estándar glibc/POSIX)
    a = 1103515245   # Multiplicador
    c = 12345        # Incremento aditivo
    m = 2**32        # Módulo (2^32)

    def __init__(self, semilla: int) -> None:
        """
        Inicializa el generador con una semilla.
        
        Args:
            semilla: Valor inicial (entero) que determina la secuencia.
        """
        self.Xo = int(semilla) % self.m
        if self.Xo == 0:
            self.Xo = 1

    def siguiente(self) -> int:
        """
        Genera el siguiente número entero de la secuencia.
        
        Implementa: X_n = (a * X_o + c) mod m
        
        Returns:
            Número entero sin signo entre 0 y m-1.
        """
        self.Xo = (self.a * self.Xo + self.c) % self.m
        return self.Xo

    def next_float(self) -> float:
        """
        Genera un número decimal entre 0.0 y 1.0 (exclusivo).
        
        Returns:
            float: Número normalizado en rango [0.0, 1.0)
        """
        return self.siguiente() / self.m

    def randint(self, min_val: int, max_val: int) -> int:
        """
        Genera un número entero dentro de un rango específico [min_val, max_val].
        
        Args:
            min_val: Límite inferior (inclusivo)
            max_val: Límite superior (inclusivo)
        
        Returns:
            int: Número aleatorio en el rango solicitado.
        
        Raises:
            ValueError: Si min_val >= max_val
        """
        if min_val >= max_val:
            raise ValueError(f"min_val ({min_val}) debe ser < max_val ({max_val})")
        
        rango = max_val - min_val + 1
        return min_val + int(self.next_float() * rango)

    def choice(self, lista: list):
        """
        Selecciona un elemento aleatorio de una lista.
        
        Args:
            lista: Lista de elementos para elegir.
        
        Returns:
            Elemento aleatorio de la lista, o None si está vacía.
        """
        if not lista:
            return None
        
        indice = self.randint(0, len(lista) - 1)
        return lista[indice]

    def set_seed(self, semilla: int) -> None:
        """
        Reinicia el generador con una nueva semilla.
        
        Args:
            semilla: Nueva semilla (entero).
        """
        self.__init__(semilla)


# ============================================================================
# SCRIPT DE PRUEBA (Sintaxis similar a notebooks educativos)
# ============================================================================

if __name__ == "__main__":
    print("=" * 75)
    print("GENERADOR DE NÚMEROS PSEUDOALEATORIOS - MÉTODO CONGRUENCIAL LINEAL (LCG)")
    print("=" * 75)
    
    # Parámetros del LCG
    a = 1103515245
    c = 12345
    m = 2**32
    Xo = 12345  # Semilla inicial
    
    print(f"\nParámetros del LCG:")
    print(f"  a (Multiplicador):  {a}")
    print(f"  c (Incremento):     {c}")
    print(f"  m (Módulo):         {m}")
    print(f"  Xo (Semilla):       {Xo}")
    
    # Test 1: Generando números decimales
    print("\n" + "-" * 75)
    print("TEST 1: Generando 10 números decimales [0.0, 1.0)")
    print("-" * 75)
    
    prng = LCG(Xo)
    for i in range(10):
        numero = prng.next_float()
        print(f"{i+1:2d}. {numero:.10f}")
    
    # Test 2: Generando números enteros en rango (dado)
    print("\n" + "-" * 75)
    print("TEST 2: Simulando 20 tiradas de dado (1 a 6)")
    print("-" * 75)
    
    prng.set_seed(Xo)
    for i in range(20):
        numero = prng.randint(1, 6)
        print(f"Tirada {i+1:2d}: {numero}")
    
    # Test 3: Selección de elementos de lista
    print("\n" + "-" * 75)
    print("TEST 3: Eligiendo colores aleatorios de una lista")
    print("-" * 75)
    
    prng.set_seed(Xo)
    colores = ["Rojo", "Azul", "Verde", "Amarillo", "Púrpura", "Naranja"]
    
    for i in range(10):
        color = prng.choice(colores)
        print(f"{i+1:2d}. Color: {color}")
    
    # Test 4: Verificando reproducibilidad
    print("\n" + "-" * 75)
    print("TEST 4: Verificando reproducibilidad (misma semilla = misma secuencia)")
    print("-" * 75)
    
    prng1 = LCG(99999)
    secuencia1 = [prng1.next_float() for _ in range(5)]
    
    prng2 = LCG(99999)
    secuencia2 = [prng2.next_float() for _ in range(5)]
    
    print("\nSecuencia 1:")
    for i, val in enumerate(secuencia1, 1):
        print(f"  {i}. {val:.10f}")
    
    print("\nSecuencia 2 (misma semilla):")
    for i, val in enumerate(secuencia2, 1):
        print(f"  {i}. {val:.10f}")
    
    if secuencia1 == secuencia2:
        print("\n✓ REPRODUCIBILIDAD VERIFICADA: Ambas secuencias son idénticas")
    else:
        print("\n✗ ERROR: Las secuencias no coinciden")
    
    # Test 5: Usando en contexto del juego (mapas aleatorios)
    print("\n" + "-" * 75)
    print("TEST 5: Seleccionando mapas aleatorios para Duck Hunt")
    print("-" * 75)
    
    prng.set_seed(int(__import__('time').time() * 1000000) % (2**32))
    mapas = ["Bosque", "Montaña", "Pantano", "Playa", "Castillo"]
    
    for ronda in range(5):
        mapa = prng.choice(mapas)
        print(f"Ronda {ronda+1}: Mapa -> {mapa}")
    
    print("\n" + "=" * 75)
    print("PRUEBAS COMPLETADAS EXITOSAMENTE")
    print("=" * 75)
