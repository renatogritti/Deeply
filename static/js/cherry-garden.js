class CherryGarden {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(50, this.canvas.clientWidth / this.canvas.clientHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ 
            canvas: this.canvas, 
            antialias: true, 
            alpha: true 
        });
        this.trees = [];
        this.petals = [];
        
        this.init();
        this.animate();
    }

    init() {
        // Configuração do renderer com tamanho adequado
        const width = this.canvas.clientWidth;
        const height = this.canvas.clientHeight;
        this.renderer.setSize(width, height);
        this.renderer.setClearColor(0xffffff, 0);

        // Ajustar câmera para uma melhor visualização inicial
        this.camera.position.set(0, 15, 25);
        this.camera.lookAt(0, 5, 0);

        // Luzes mais suaves e bem posicionadas
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 20, 10);
        this.scene.add(ambientLight, directionalLight);

        // Chão centralizado e maior
        const planeGeometry = new THREE.PlaneGeometry(50, 50);
        const planeMaterial = new THREE.MeshStandardMaterial({ 
            color: 0xe8f5e9,
            side: THREE.DoubleSide
        });
        const plane = new THREE.Mesh(planeGeometry, planeMaterial);
        plane.rotation.x = -Math.PI / 2;
        plane.position.y = 0;
        this.scene.add(plane);

        // Criar pétalas
        this.createPetals();

        // Ajuste responsivo
        window.addEventListener('resize', () => {
            const newWidth = this.canvas.clientWidth;
            const newHeight = this.canvas.clientHeight;
            
            this.camera.aspect = newWidth / newHeight;
            this.camera.updateProjectionMatrix();
            
            this.renderer.setSize(newWidth, newHeight, false);
        }, false);
    }

    createPetals() {
        const petalGeometry = new THREE.PlaneGeometry(0.2, 0.2);
        const petalMaterial = new THREE.MeshBasicMaterial({
            color: 0xffb7c5,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.7
        });

        for (let i = 0; i < 50; i++) {
            const petal = new THREE.Mesh(petalGeometry, petalMaterial);
            this.resetPetal(petal);
            this.petals.push(petal);
            this.scene.add(petal);
        }
    }

    resetPetal(petal) {
        petal.position.set(
            (Math.random() - 0.5) * 30,
            15,
            (Math.random() - 0.5) * 30
        );
        petal.rotation.set(
            Math.random() * Math.PI,
            Math.random() * Math.PI,
            Math.random() * Math.PI
        );
        petal.userData.speedY = Math.random() * 0.05 + 0.02;
        petal.userData.speedRotation = Math.random() * 0.02;
    }

    createTree(type, position) {
        const treeGroup = new THREE.Group();
        
        // Tronco
        const trunkGeometry = new THREE.CylinderGeometry(0.2, 0.3, 2, 8);
        const trunkMaterial = new THREE.MeshStandardMaterial({ color: 0x8b4513 });
        const trunk = new THREE.Mesh(trunkGeometry, trunkMaterial);
        trunk.position.y = 1;
        treeGroup.add(trunk);

        // Copa
        const size = type === 'blooming' ? 1.5 : 
                    type === 'tree' ? 1.2 :
                    type === 'sapling' ? 0.8 : 0.4;

        const crownGeometry = new THREE.SphereGeometry(size, 16, 16);
        const crownMaterial = new THREE.MeshStandardMaterial({ 
            color: type === 'seed' ? 0x90EE90 : 0xffb7c5 
        });
        const crown = new THREE.Mesh(crownGeometry, crownMaterial);
        crown.position.y = 2 + size/2;
        treeGroup.add(crown);

        // Posicionar árvore
        treeGroup.position.set(position.x, position.y, position.z);
        return treeGroup;
    }

    updateGarden(data) {
        // Limpar árvores existentes
        this.trees.forEach(tree => this.scene.remove(tree));
        this.trees = [];

        const activeData = data.values.filter(v => v > 0);
        
        // Ajustar raio baseado no número de árvores
        const radius = Math.max(8, Math.min(activeData.length * 0.8, 12));

        activeData.forEach((minutes, index) => {
            const angle = (index / activeData.length) * Math.PI * 2;
            const x = Math.cos(angle) * radius;
            const z = Math.sin(angle) * radius;

            const tree = this.createTree(this.getTreeType(minutes), { x, y: 0, z });
            this.scene.add(tree);
            this.trees.push(tree);

            // Animação de crescimento mais suave
            tree.scale.set(0.01, 0.01, 0.01);
            gsap.to(tree.scale, {
                x: 1,
                y: 1,
                z: 1,
                duration: 1.2,
                ease: "elastic.out(1, 0.5)",
                delay: index * 0.1
            });
        });

        // Ajustar câmera de forma mais suave
        const cameraDistance = Math.max(15, radius * 1.8);
        gsap.to(this.camera.position, {
            x: cameraDistance * 0.5,
            y: cameraDistance * 0.4,
            z: cameraDistance,
            duration: 2,
            ease: "power2.inOut",
            onUpdate: () => {
                this.camera.lookAt(0, 2, 0);
            }
        });
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        // Animar pétalas
        this.petals.forEach(petal => {
            petal.position.y -= petal.userData.speedY;
            petal.rotation.x += petal.userData.speedRotation;
            petal.rotation.z += petal.userData.speedRotation;

            if (petal.position.y < 0) {
                this.resetPetal(petal);
            }
        });

        this.renderer.render(this.scene, this.camera);
    }

    onWindowResize() {
        this.camera.aspect = this.canvas.clientWidth / this.canvas.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.canvas.clientWidth, this.canvas.clientHeight);
    }

    getTreeType(minutes) {
        // Broto: menos de 30 minutos
        if (minutes < 30) return 'seed';
        // Jovem: 30-60 minutos
        if (minutes < 60) return 'sapling';
        // Adulta: 1-2 horas
        if (minutes < 120) return 'tree';
        // Florescendo: mais de 2 horas
        return 'blooming';
    }
}

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('cherry-garden')) {
        window.cherryGarden = new CherryGarden('cherry-garden');
    }
});
