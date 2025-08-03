// Particle Background Animation System
class ParticleSystem {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.warn(`Particle container ${containerId} not found`);
            return;
        }

        // Configuration
        this.config = {
            particleCount: options.particleCount || 100,
            particleSize: options.particleSize || 2,
            speed: options.speed || 0.5,
            connectionDistance: options.connectionDistance || 120,
            colors: options.colors || ['#00d4ff', '#0099cc', '#00b8d4', '#0066cc'],
            opacity: options.opacity || 0.7,
            ...options
        };

        this.particles = [];
        this.animationId = null;
        this.mouse = { x: 0, y: 0 };
        this.isRunning = false;

        this.init();
    }

    init() {
        this.createCanvas();
        this.createParticles();
        this.bindEvents();
        this.start();
    }

    createCanvas() {
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('2d');
        
        this.canvas.style.position = 'absolute';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.pointerEvents = 'none';
        this.canvas.style.zIndex = '1';
        
        this.container.appendChild(this.canvas);
        this.resize();
    }

    createParticles() {
        this.particles = [];
        
        for (let i = 0; i < this.config.particleCount; i++) {
            this.particles.push(new Particle(
                Math.random() * this.canvas.width,
                Math.random() * this.canvas.height,
                this.config
            ));
        }
    }

    bindEvents() {
        window.addEventListener('resize', () => this.resize());
        
        // Mouse interaction
        this.container.addEventListener('mousemove', (e) => {
            const rect = this.container.getBoundingClientRect();
            this.mouse.x = e.clientX - rect.left;
            this.mouse.y = e.clientY - rect.top;
        });

        this.container.addEventListener('mouseleave', () => {
            this.mouse.x = -1000;
            this.mouse.y = -1000;
        });
    }

    resize() {
        const rect = this.container.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
        
        // Redistribute particles on resize
        this.particles.forEach(particle => {
            if (particle.x > this.canvas.width) particle.x = this.canvas.width;
            if (particle.y > this.canvas.height) particle.y = this.canvas.height;
        });
    }

    update() {
        this.particles.forEach(particle => {
            particle.update(this.canvas.width, this.canvas.height, this.mouse);
        });
    }

    draw() {
        // Clear canvas with fade effect
        this.ctx.fillStyle = 'rgba(10, 15, 25, 0.05)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw connections
        this.drawConnections();

        // Draw particles
        this.particles.forEach(particle => {
            particle.draw(this.ctx);
        });
    }

    drawConnections() {
        for (let i = 0; i < this.particles.length; i++) {
            for (let j = i + 1; j < this.particles.length; j++) {
                const dx = this.particles[i].x - this.particles[j].x;
                const dy = this.particles[i].y - this.particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < this.config.connectionDistance) {
                    const opacity = (1 - distance / this.config.connectionDistance) * 0.3;
                    
                    this.ctx.strokeStyle = `rgba(0, 212, 255, ${opacity})`;
                    this.ctx.lineWidth = 0.5;
                    this.ctx.beginPath();
                    this.ctx.moveTo(this.particles[i].x, this.particles[i].y);
                    this.ctx.lineTo(this.particles[j].x, this.particles[j].y);
                    this.ctx.stroke();
                }
            }
        }

        // Draw mouse connections
        if (this.mouse.x > 0 && this.mouse.y > 0) {
            this.particles.forEach(particle => {
                const dx = particle.x - this.mouse.x;
                const dy = particle.y - this.mouse.y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < this.config.connectionDistance * 1.5) {
                    const opacity = (1 - distance / (this.config.connectionDistance * 1.5)) * 0.6;
                    
                    this.ctx.strokeStyle = `rgba(0, 212, 255, ${opacity})`;
                    this.ctx.lineWidth = 1;
                    this.ctx.beginPath();
                    this.ctx.moveTo(particle.x, particle.y);
                    this.ctx.lineTo(this.mouse.x, this.mouse.y);
                    this.ctx.stroke();
                }
            });
        }
    }

    animate() {
        if (!this.isRunning) return;
        
        this.update();
        this.draw();
        this.animationId = requestAnimationFrame(() => this.animate());
    }

    start() {
        if (this.isRunning) return;
        this.isRunning = true;
        this.animate();
    }

    stop() {
        this.isRunning = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }

    destroy() {
        this.stop();
        if (this.canvas && this.canvas.parentNode) {
            this.canvas.parentNode.removeChild(this.canvas);
        }
        window.removeEventListener('resize', this.resize);
    }
}

class Particle {
    constructor(x, y, config) {
        this.x = x;
        this.y = y;
        this.size = Math.random() * config.particleSize + 1;
        this.speedX = (Math.random() - 0.5) * config.speed;
        this.speedY = (Math.random() - 0.5) * config.speed;
        this.color = config.colors[Math.floor(Math.random() * config.colors.length)];
        this.opacity = Math.random() * config.opacity + 0.3;
        this.baseSize = this.size;
        this.pulse = Math.random() * Math.PI * 2;
    }

    update(canvasWidth, canvasHeight, mouse) {
        // Update position
        this.x += this.speedX;
        this.y += this.speedY;

        // Bounce off walls
        if (this.x <= 0 || this.x >= canvasWidth) {
            this.speedX *= -0.8;
            this.x = Math.max(0, Math.min(canvasWidth, this.x));
        }
        if (this.y <= 0 || this.y >= canvasHeight) {
            this.speedY *= -0.8;
            this.y = Math.max(0, Math.min(canvasHeight, this.y));
        }

        // Mouse interaction
        if (mouse.x > 0 && mouse.y > 0) {
            const dx = mouse.x - this.x;
            const dy = mouse.y - this.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < 100) {
                const force = (100 - distance) / 100;
                this.speedX -= (dx / distance) * force * 0.01;
                this.speedY -= (dy / distance) * force * 0.01;
            }
        }

        // Pulse effect
        this.pulse += 0.02;
        this.size = this.baseSize + Math.sin(this.pulse) * 0.5;

        // Damping
        this.speedX *= 0.99;
        this.speedY *= 0.99;
    }

    draw(ctx) {
        ctx.save();
        
        // Glow effect
        ctx.shadowColor = this.color;
        ctx.shadowBlur = 10;
        
        // Draw particle
        ctx.globalAlpha = this.opacity;
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
        
        // Inner bright core
        ctx.shadowBlur = 0;
        ctx.globalAlpha = this.opacity * 1.5;
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size * 0.3, 0, Math.PI * 2);
        ctx.fill();
        
        ctx.restore();
    }
}

// Initialize particle system when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if the particles container exists
    const particlesContainer = document.getElementById('particles-bg');
    if (particlesContainer) {
        window.particleSystem = new ParticleSystem('particles-bg', {
            particleCount: window.innerWidth < 768 ? 50 : 100, // Fewer particles on mobile
            particleSize: 3,
            speed: 0.3,
            connectionDistance: 120,
            colors: ['#00d4ff', '#0099cc', '#00b8d4', '#0066cc', '#00ffcc'],
            opacity: 0.8
        });
    }
});

// Performance optimization: pause particles when tab is not visible
document.addEventListener('visibilitychange', () => {
    if (window.particleSystem) {
        if (document.hidden) {
            window.particleSystem.stop();
        } else {
            window.particleSystem.start();
        }
    }
});