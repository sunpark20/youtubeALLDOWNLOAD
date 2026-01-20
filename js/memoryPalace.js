export default class MemoryPalace {
    constructor(scene) {
        this.scene = scene;
    }

    create() {
        this.createFloor();
        this.createWalls();
        this.createFurniture();
        this.createDecorations();
    }

    createFloor() {
        // Main floor
        const floorGeometry = new THREE.PlaneGeometry(20, 20);
        const floorMaterial = new THREE.MeshStandardMaterial({
            color: 0x8b7355,
            roughness: 0.8,
            metalness: 0.2
        });
        const floor = new THREE.Mesh(floorGeometry, floorMaterial);
        floor.rotation.x = -Math.PI / 2;
        floor.receiveShadow = true;
        this.scene.add(floor);

        // Floor tiles pattern
        const tileGeometry = new THREE.PlaneGeometry(2, 2);
        const tileMaterial1 = new THREE.MeshStandardMaterial({
            color: 0x6b5345,
            roughness: 0.9
        });
        const tileMaterial2 = new THREE.MeshStandardMaterial({
            color: 0x9b8375,
            roughness: 0.9
        });

        for (let x = -4; x <= 4; x++) {
            for (let z = -4; z <= 4; z++) {
                const tile = new THREE.Mesh(
                    tileGeometry,
                    (x + z) % 2 === 0 ? tileMaterial1 : tileMaterial2
                );
                tile.rotation.x = -Math.PI / 2;
                tile.position.set(x * 2, 0.01, z * 2);
                tile.receiveShadow = true;
                this.scene.add(tile);
            }
        }
    }

    createWalls() {
        const wallHeight = 4;
        const wallThickness = 0.2;
        const roomSize = 20;

        const wallMaterial = new THREE.MeshStandardMaterial({
            color: 0xe8d4b8,
            roughness: 0.9
        });

        // Back wall
        const backWall = this.createWall(roomSize, wallHeight, wallThickness, wallMaterial);
        backWall.position.set(0, wallHeight / 2, -roomSize / 2);
        this.scene.add(backWall);

        // Left wall
        const leftWall = this.createWall(wallThickness, wallHeight, roomSize, wallMaterial);
        leftWall.position.set(-roomSize / 2, wallHeight / 2, 0);
        this.scene.add(leftWall);

        // Right wall
        const rightWall = this.createWall(wallThickness, wallHeight, roomSize, wallMaterial);
        rightWall.position.set(roomSize / 2, wallHeight / 2, 0);
        this.scene.add(rightWall);

        // Front walls (with opening)
        const frontWallLeft = this.createWall(7, wallHeight, wallThickness, wallMaterial);
        frontWallLeft.position.set(-6.5, wallHeight / 2, roomSize / 2);
        this.scene.add(frontWallLeft);

        const frontWallRight = this.createWall(7, wallHeight, wallThickness, wallMaterial);
        frontWallRight.position.set(6.5, wallHeight / 2, roomSize / 2);
        this.scene.add(frontWallRight);

        const frontWallTop = this.createWall(6, 1.5, wallThickness, wallMaterial);
        frontWallTop.position.set(0, wallHeight - 0.75, roomSize / 2);
        this.scene.add(frontWallTop);
    }

    createWall(width, height, depth, material) {
        const geometry = new THREE.BoxGeometry(width, height, depth);
        const wall = new THREE.Mesh(geometry, material);
        wall.castShadow = true;
        wall.receiveShadow = true;
        return wall;
    }

    createFurniture() {
        // Pedestals for memory objects
        const pedestalGeometry = new THREE.CylinderGeometry(0.4, 0.5, 1, 8);
        const pedestalMaterial = new THREE.MeshStandardMaterial({
            color: 0x8b4513,
            roughness: 0.7
        });

        const positions = [
            { x: -6, z: -6 },
            { x: -6, z: 0 },
            { x: -6, z: 6 },
            { x: 0, z: -6 },
            { x: 0, z: 6 },
            { x: 6, z: -6 },
            { x: 6, z: 0 },
            { x: 6, z: 6 }
        ];

        positions.forEach(pos => {
            const pedestal = new THREE.Mesh(pedestalGeometry, pedestalMaterial);
            pedestal.position.set(pos.x, 0.5, pos.z);
            pedestal.castShadow = true;
            pedestal.receiveShadow = true;
            this.scene.add(pedestal);

            // Add a small label plate
            const plateGeometry = new THREE.CylinderGeometry(0.42, 0.42, 0.05, 8);
            const plateMaterial = new THREE.MeshStandardMaterial({
                color: 0xd4af37,
                roughness: 0.3,
                metalness: 0.8
            });
            const plate = new THREE.Mesh(plateGeometry, plateMaterial);
            plate.position.set(pos.x, 1.025, pos.z);
            this.scene.add(plate);
        });

        // Central table
        const tableTopGeometry = new THREE.BoxGeometry(3, 0.1, 3);
        const tableTopMaterial = new THREE.MeshStandardMaterial({
            color: 0x654321,
            roughness: 0.5
        });
        const tableTop = new THREE.Mesh(tableTopGeometry, tableTopMaterial);
        tableTop.position.set(0, 1, 0);
        tableTop.castShadow = true;
        tableTop.receiveShadow = true;
        this.scene.add(tableTop);

        // Table legs
        const legGeometry = new THREE.CylinderGeometry(0.1, 0.1, 1);
        const legMaterial = new THREE.MeshStandardMaterial({
            color: 0x4a3020,
            roughness: 0.7
        });

        const legPositions = [
            { x: -1.3, z: -1.3 },
            { x: -1.3, z: 1.3 },
            { x: 1.3, z: -1.3 },
            { x: 1.3, z: 1.3 }
        ];

        legPositions.forEach(pos => {
            const leg = new THREE.Mesh(legGeometry, legMaterial);
            leg.position.set(pos.x, 0.5, pos.z);
            leg.castShadow = true;
            this.scene.add(leg);
        });
    }

    createDecorations() {
        // Windows
        const windowGeometry = new THREE.PlaneGeometry(2, 2.5);
        const windowMaterial = new THREE.MeshStandardMaterial({
            color: 0x87ceeb,
            transparent: true,
            opacity: 0.3,
            side: THREE.DoubleSide
        });

        // Left wall windows
        for (let i = -1; i <= 1; i++) {
            const window1 = new THREE.Mesh(windowGeometry, windowMaterial);
            window1.position.set(-9.89, 2.25, i * 5);
            window1.rotation.y = Math.PI / 2;
            this.scene.add(window1);
        }

        // Back wall windows
        for (let i = -1; i <= 1; i++) {
            const window2 = new THREE.Mesh(windowGeometry, windowMaterial);
            window2.position.set(i * 5, 2.25, -9.89);
            this.scene.add(window2);
        }

        // Ceiling light
        const lightGeometry = new THREE.SphereGeometry(0.3, 16, 16);
        const lightMaterial = new THREE.MeshBasicMaterial({
            color: 0xffffcc,
            emissive: 0xffffcc
        });
        const ceilingLight = new THREE.Mesh(lightGeometry, lightMaterial);
        ceilingLight.position.set(0, 3.5, 0);
        this.scene.add(ceilingLight);

        const pointLight = new THREE.PointLight(0xffffcc, 1, 20);
        pointLight.position.copy(ceilingLight.position);
        this.scene.add(pointLight);
    }
}
