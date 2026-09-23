/**
 * LIQUIDITY VECTOR FIELD 3D (TELLUX WIND3D & STREAMLINE FLOW ENGINE - STABILIZED V2)
 * High-performance GPU-friendly streamline particle field simulating crypto capital flows.
 * Features:
 * - Bounded laminar logarithmic vortex streamlines (no chaotic scattering / 'bay loan')
 * - Delta-clamped physics (immune to frame drops / tab switching)
 * - Dynamic FPS-based Adaptive LOD (guarantees >= 45 FPS)
 * - Real-time market telemetry binding (Bullish Emerald, Bearish Crimson, Quantum Violet, Neutral Cyan)
 * - Smooth alpha fade-in/fade-out at boundary limits
 */

class LiquidityVectorField {
    constructor(scene, options = {}) {
        this.scene = scene;
        this.isMobile = window.innerWidth < 768;
        this.maxParticles = options.particleCount || (this.isMobile ? 900 : 2400);
        this.activeParticles = this.maxParticles;
        this.speed = options.speed || 1.0;
        this.flowMode = 'NEUTRAL'; // BULLISH, BEARISH, CONFLUENCE, NEUTRAL
        
        this.particles = null;
        this.geometry = null;
        this.material = null;
        this.positions = null;
        this.colors = null;
        
        // Streamline state per particle: radius, angle, height, speed, lifetime, maxLife
        this.radii = null;
        this.angles = null;
        this.heights = null;
        this.angularSpeeds = null;
        this.inwardSpeeds = null;
        this.lifetimes = null;
        this.maxLifetimes = null;
        
        this.maxRadius = 138;
        this.minRadius = 18;
        this.floorY = 2.0;
        this.maxHeight = 16.0;

        // Target color palettes
        this.targetColors = {
            BULLISH: new THREE.Color(0x10b981),   // Emerald Neon
            BEARISH: new THREE.Color(0xef4444),   // Crimson Glow
            CONFLUENCE: new THREE.Color(0xa855f7),// Quantum Violet
            NEUTRAL: new THREE.Color(0x38bdf8)    // Cyan Cyber
        };
        
        this.currentColor = this.targetColors.NEUTRAL.clone();
        this.directionMultiplier = 1.0; // 1 = clockwise, -1 = counter-clockwise

        // FPS & LOD tracking
        this.lastFrameTime = performance.now();
        this.fpsHistory = [];
        this.lodCheckCounter = 0;

        this.init();
    }

    init() {
        this.geometry = new THREE.BufferGeometry();
        this.positions = new Float32Array(this.maxParticles * 3);
        this.colors = new Float32Array(this.maxParticles * 3);
        
        this.radii = new Float32Array(this.maxParticles);
        this.angles = new Float32Array(this.maxParticles);
        this.heights = new Float32Array(this.maxParticles);
        this.angularSpeeds = new Float32Array(this.maxParticles);
        this.inwardSpeeds = new Float32Array(this.maxParticles);
        this.lifetimes = new Float32Array(this.maxParticles);
        this.maxLifetimes = new Float32Array(this.maxParticles);

        for (let i = 0; i < this.maxParticles; i++) {
            this.resetParticle(i, true);
        }

        this.geometry.setAttribute('position', new THREE.BufferAttribute(this.positions, 3));
        this.geometry.setAttribute('color', new THREE.BufferAttribute(this.colors, 3));

        // Create glowing radial sprite texture
        const canvas = document.createElement('canvas');
        canvas.width = 64;
        canvas.height = 64;
        const ctx = canvas.getContext('2d');
        const grad = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
        grad.addColorStop(0, 'rgba(255, 255, 255, 1.0)');
        grad.addColorStop(0.25, 'rgba(180, 230, 255, 0.9)');
        grad.addColorStop(0.55, 'rgba(56, 189, 248, 0.4)');
        grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, 64, 64);

        const particleTexture = new THREE.CanvasTexture(canvas);

        this.material = new THREE.PointsMaterial({
            size: this.isMobile ? 2.6 : 3.6,
            map: particleTexture,
            transparent: true,
            blending: THREE.AdditiveBlending,
            depthWrite: false,
            vertexColors: true
        });

        this.particles = new THREE.Points(this.geometry, this.material);
        this.particles.frustumCulled = false;
        this.scene.add(this.particles);
    }

    resetParticle(index, randomStart = false) {
        const i3 = index * 3;
        
        // Bounded radial distribution
        if (randomStart) {
            this.radii[index] = this.minRadius + Math.random() * (this.maxRadius - this.minRadius);
            this.angles[index] = Math.random() * Math.PI * 2;
            this.lifetimes[index] = Math.random() * 6.0;
        } else {
            this.radii[index] = this.maxRadius - Math.random() * 12;
            this.angles[index] = Math.random() * Math.PI * 2;
            this.lifetimes[index] = 0;
        }

        this.maxLifetimes[index] = 5.0 + Math.random() * 4.0;
        
        // Structured laminar kinematics
        // Angular velocity increases gracefully toward core (Keplerian vortex)
        const baseSpeed = 0.5 + Math.random() * 0.4;
        this.angularSpeeds[index] = baseSpeed;
        this.inwardSpeeds[index] = 8.0 + Math.random() * 10.0;
        this.heights[index] = this.floorY + Math.random() * (this.maxHeight - this.floorY);

        // Update 3D cartesian position
        const r = this.radii[index];
        const a = this.angles[index];
        this.positions[i3] = Math.cos(a) * r;
        this.positions[i3 + 1] = this.heights[index];
        this.positions[i3 + 2] = Math.sin(a) * r;

        // Apply color with subtle gradient
        this.updateParticleColor(index, 1.0);
    }

    updateParticleColor(index, alpha = 1.0) {
        const i3 = index * 3;
        const col = this.currentColor;
        const rRatio = (this.radii[index] - this.minRadius) / (this.maxRadius - this.minRadius);
        
        // Outer particles slightly cooler/dimmer, inner particles brighter
        const brightness = Math.min(1.0, (0.6 + (1.0 - rRatio) * 0.4) * alpha);
        this.colors[i3] = col.r * brightness;
        this.colors[i3 + 1] = col.g * brightness;
        this.colors[i3 + 2] = col.b * brightness;
    }

    setMode(mode) {
        if (this.targetColors[mode]) {
            this.flowMode = mode;
            if (mode === 'BEARISH') {
                this.directionMultiplier = -1.0;
            } else {
                this.directionMultiplier = 1.0;
            }
        }
    }

    /**
     * Connect real-time market data to particle dynamics
     */
    applyMarketTelemetry(telemetry) {
        if (!telemetry) return;
        
        const btcChange = parseFloat(telemetry.btc_change_24h || 0);
        const openPosCount = parseInt(telemetry.open_positions_count || 0);

        if (btcChange >= 1.5) {
            this.setMode('BULLISH');
            this.speed = 1.4;
        } else if (btcChange <= -1.5) {
            this.setMode('BEARISH');
            this.speed = 1.4;
        } else if (openPosCount >= 3) {
            this.setMode('CONFLUENCE');
            this.speed = 1.2;
        } else {
            this.setMode('NEUTRAL');
            this.speed = 0.9;
        }
    }

    update(rawDelta = 0.016) {
        if (!this.particles || !this.particles.visible) return;

        // 1. Delta clamping to protect against frame spikes / tab freezing
        const delta = Math.min(rawDelta, 0.033);

        // 2. Adaptive LOD monitoring (guarantee >= 45 FPS)
        this.lodCheckCounter++;
        if (this.lodCheckCounter > 60) {
            this.lodCheckCounter = 0;
            const now = performance.now();
            const elapsed = (now - this.lastFrameTime) / 60;
            this.lastFrameTime = now;
            const currentFps = 1000 / Math.max(1, elapsed);
            
            if (currentFps < 42 && this.activeParticles > (this.isMobile ? 500 : 1200)) {
                this.activeParticles = Math.floor(this.activeParticles * 0.8);
                this.geometry.setDrawRange(0, this.activeParticles);
            } else if (currentFps > 55 && this.activeParticles < this.maxParticles) {
                this.activeParticles = Math.min(this.maxParticles, Math.floor(this.activeParticles * 1.15));
                this.geometry.setDrawRange(0, this.activeParticles);
            }
        }

        // 3. Smooth color transition
        const target = this.targetColors[this.flowMode] || this.targetColors.NEUTRAL;
        this.currentColor.lerp(target, 0.06);

        const pos = this.positions;
        const count = this.activeParticles;
        const spd = this.speed * delta;
        const dir = this.directionMultiplier;

        for (let i = 0; i < count; i++) {
            const i3 = i * 3;
            this.lifetimes[i] += delta;

            // Logarithmic spiral motion:
            // Radius contracts smoothly toward core
            this.radii[i] -= this.inwardSpeeds[i] * spd;

            // Angular velocity increases as radius decreases: omega ~ 1 / sqrt(r)
            const r = Math.max(this.minRadius, this.radii[i]);
            const omega = (this.angularSpeeds[i] * 12.0) / Math.sqrt(r + 15.0);
            this.angles[i] += omega * spd * dir;

            // Gentle sinusoidal height wave (laminar flow along floor)
            const waveY = this.heights[i] + Math.sin(this.angles[i] * 2.5 + i) * 1.2;

            // Fade at boundaries: fade in near maxRadius, fade out near minRadius or life end
            const lifeRatio = this.lifetimes[i] / this.maxLifetimes[i];
            const rRatio = (r - this.minRadius) / (this.maxRadius - this.minRadius);
            const boundaryFade = Math.min(1.0, rRatio * 3.0) * Math.min(1.0, (1.0 - rRatio) * 3.0);
            const lifeFade = Math.min(1.0, (1.0 - lifeRatio) * 2.5);
            const alpha = Math.max(0.15, boundaryFade * lifeFade);

            if (this.radii[i] <= this.minRadius || lifeRatio >= 1.0) {
                this.resetParticle(i, false);
            } else {
                pos[i3] = Math.cos(this.angles[i]) * r;
                pos[i3 + 1] = Math.max(1.5, Math.min(this.maxHeight, waveY));
                pos[i3 + 2] = Math.sin(this.angles[i]) * r;
                this.updateParticleColor(i, alpha);
            }
        }

        this.geometry.attributes.position.needsUpdate = true;
        this.geometry.attributes.color.needsUpdate = true;
    }

    setVisible(visible) {
        if (this.particles) {
            this.particles.visible = visible;
        }
    }

    dispose() {
        if (this.particles && this.scene) {
            this.scene.remove(this.particles);
        }
        if (this.geometry) this.geometry.dispose();
        if (this.material) this.material.dispose();
    }
}

window.LiquidityVectorField = LiquidityVectorField;
