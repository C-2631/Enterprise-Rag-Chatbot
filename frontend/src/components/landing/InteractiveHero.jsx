import { useEffect, useRef } from "react";

function InteractiveHero() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    // 3D projections parameters
    const particleCount = 100; // Increased density slightly for a richer experience
    const particles = [];
    const maxDistance = 160; // Distance to draw lines
    const focalLength = 320;

    // Mouse coordinates:
    // mouse3D for camera rotation, mouseScreen for repulsion physics
    let mouse3D = { x: 0, y: 0, targetX: 0, targetY: 0 };
    let mouseScreen = { x: -1000, y: -1000, targetX: -1000, targetY: -1000 }; // Starts offscreen

    // Initialize 3D particles
    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: (Math.random() - 0.5) * 850,
        y: (Math.random() - 0.5) * 650,
        z: (Math.random() - 0.5) * 850,
        baseX: (Math.random() - 0.5) * 850,
        baseY: (Math.random() - 0.5) * 650,
        baseZ: (Math.random() - 0.5) * 850,
        offsetX: 0,
        offsetY: 0,
        speed: 0.2 + Math.random() * 0.6,
        angle: Math.random() * Math.PI * 2,
        driftOffset: Math.random() * 100,
      });
    }

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    const handleMouseMove = (e) => {
      // Camera rotation mouse targeting
      mouse3D.targetX = e.clientX - width / 2;
      mouse3D.targetY = e.clientY - height / 2;
      
      // Screen space physics mouse targeting
      mouseScreen.targetX = e.clientX;
      mouseScreen.targetY = e.clientY;
    };

    const handleMouseLeave = () => {
      mouseScreen.targetX = -1000;
      mouseScreen.targetY = -1000;
    };

    window.addEventListener("resize", handleResize);
    window.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseleave", handleMouseLeave);

    // Animation Loop
    const animate = () => {
      // Clear with sleek dark slate background
      ctx.fillStyle = "#0f172a";
      ctx.fillRect(0, 0, width, height);

      // Smoothly interpolate mouse coords for inertia
      mouse3D.x += (mouse3D.targetX - mouse3D.x) * 0.05;
      mouse3D.y += (mouse3D.targetY - mouse3D.y) * 0.05;
      
      if (mouseScreen.targetX !== -1000) {
        if (mouseScreen.x === -1000) {
          mouseScreen.x = mouseScreen.targetX;
          mouseScreen.y = mouseScreen.targetY;
        } else {
          mouseScreen.x += (mouseScreen.targetX - mouseScreen.x) * 0.1;
          mouseScreen.y += (mouseScreen.targetY - mouseScreen.y) * 0.1;
        }
      } else {
        mouseScreen.x = -1000;
        mouseScreen.y = -1000;
      }

      // Rotation angles based on mouse offsets + time
      const angleY = mouse3D.x * 0.00025 + Date.now() * 0.00004;
      const angleX = mouse3D.y * 0.00025;

      const cosY = Math.cos(angleY);
      const sinY = Math.sin(angleY);
      const cosX = Math.cos(angleX);
      const sinX = Math.sin(angleX);

      const projectedParticles = [];

      // Update and project particles
      for (let i = 0; i < particleCount; i++) {
        const p = particles[i];

        // Slowly drift particles (using sine waves for velocity drift)
        p.angle += 0.0015 * p.speed;
        const driftX = Math.sin(p.angle + p.driftOffset) * 20;
        const driftY = Math.cos(p.angle * 0.8 + p.driftOffset) * 20;

        let rx = p.baseX + driftX;
        let ry = p.baseY + driftY;
        let rz = p.baseZ + Math.sin(p.angle + p.driftOffset) * 15;

        // Apply 3D Rotation (around Y axis first, then X axis)
        let x1 = rx * cosY - rz * sinY;
        let z1 = rz * cosY + rx * sinY;

        let y2 = ry * cosX - z1 * sinX;
        let z2 = z1 * cosX + ry * sinX;

        // Shift depth back to avoid clipping
        z2 += 500;

        // Perspective projection
        const scale = focalLength / (focalLength + z2);
        let screenX = width / 2 + x1 * scale;
        let screenY = height / 2 + y2 * scale;

        // Repulsion physics in screen space
        if (mouseScreen.x !== -1000) {
          const dx = screenX - mouseScreen.x;
          const dy = screenY - mouseScreen.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const repulsionRadius = 160;

          if (dist < repulsionRadius) {
            // Stronger push the closer it gets
            const force = (repulsionRadius - dist) / repulsionRadius;
            const pushAngle = Math.atan2(dy, dx);
            
            // Apply spring-like force to offset vectors
            p.offsetX += Math.cos(pushAngle) * force * 12 * scale;
            p.offsetY += Math.sin(pushAngle) * force * 12 * scale;
          }
        }

        // Slowly decay the offset back to zero (damping)
        p.offsetX *= 0.93;
        p.offsetY *= 0.93;

        // Add physical offsets to final screen positions
        screenX += p.offsetX;
        screenY += p.offsetY;

        projectedParticles.push({
          x: screenX,
          y: screenY,
          z: z2,
          scale: scale,
        });
      }

      // Draw connecting lines between adjacent projected nodes
      for (let i = 0; i < particleCount; i++) {
        const p1 = projectedParticles[i];

        for (let j = i + 1; j < particleCount; j++) {
          const p2 = projectedParticles[j];

          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          // Only draw connection if close
          if (dist < maxDistance * p1.scale) {
            const alpha = (1 - dist / (maxDistance * p1.scale)) * 0.18;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            
            // Sleek modern feel: Light Blue or Indigo based on index
            if (i % 2 === 0) {
              ctx.strokeStyle = `rgba(56, 189, 248, ${alpha})`; // Light Blue 400
            } else {
              ctx.strokeStyle = `rgba(99, 102, 241, ${alpha})`; // Indigo 500
            }
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }

      // Draw particle nodes
      for (let i = 0; i < particleCount; i++) {
        const p = projectedParticles[i];
        
        const size = Math.max(1, p.scale * 3.5);
        const alpha = Math.min(1, p.scale * 0.85);

        ctx.beginPath();
        ctx.arc(p.x, p.y, size, 0, Math.PI * 2);
        
        // Modern themes: Indigo, Light Blue, or Rose
        if (i % 3 === 0) {
          ctx.fillStyle = `rgba(99, 102, 241, ${alpha})`; // Indigo 500
        } else if (i % 3 === 1) {
          ctx.fillStyle = `rgba(56, 189, 248, ${alpha})`; // Light Blue 400
        } else {
          ctx.fillStyle = `rgba(244, 63, 94, ${alpha})`; // Rose 500
        }
        ctx.fill();
        
        // Subtle outer glow
        if (p.scale > 0.55) {
          ctx.beginPath();
          ctx.arc(p.x, p.y, size * 2.2, 0, Math.PI * 2);
          ctx.fillStyle = i % 3 === 0 
            ? `rgba(99, 102, 241, ${alpha * 0.22})` 
            : i % 3 === 1
            ? `rgba(56, 189, 248, ${alpha * 0.22})`
            : `rgba(244, 63, 94, ${alpha * 0.22})`;
          ctx.fill();
        }
      }

      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    // Cleanup listeners
    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseleave", handleMouseLeave);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full block pointer-events-none z-0"
      style={{ mixBlendMode: "screen" }}
    />
  );
}

export default InteractiveHero;
