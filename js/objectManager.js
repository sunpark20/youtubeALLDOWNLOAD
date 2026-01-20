export default class ObjectManager {
    constructor(scene) {
        this.scene = scene;
        this.objects = [];
        this.selectedObject = null;
        this.hoveredObject = null;
    }

    createObject(position, text = '새 객체', color = 0x4ecdc4, shape = 'box') {
        let geometry;

        switch (shape) {
            case 'sphere':
                geometry = new THREE.SphereGeometry(0.3, 32, 32);
                break;
            case 'cylinder':
                geometry = new THREE.CylinderGeometry(0.2, 0.2, 0.6, 32);
                break;
            case 'cone':
                geometry = new THREE.ConeGeometry(0.25, 0.6, 32);
                break;
            case 'box':
            default:
                geometry = new THREE.BoxGeometry(0.5, 0.5, 0.5);
                break;
        }

        const material = new THREE.MeshStandardMaterial({
            color: color,
            roughness: 0.5,
            metalness: 0.3
        });

        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.copy(position);
        mesh.castShadow = true;
        mesh.receiveShadow = true;

        // Add glow outline
        const outlineGeometry = geometry.clone();
        const outlineMaterial = new THREE.MeshBasicMaterial({
            color: 0xffffff,
            side: THREE.BackSide,
            transparent: true,
            opacity: 0
        });
        const outline = new THREE.Mesh(outlineGeometry, outlineMaterial);
        outline.scale.multiplyScalar(1.1);
        mesh.add(outline);

        // Store object data
        mesh.userData = {
            text: text,
            color: color,
            shape: shape,
            id: this.generateId(),
            outline: outline
        };

        this.scene.add(mesh);
        this.objects.push(mesh);

        // Create floating text label
        this.createTextLabel(mesh, text);

        this.saveToStorage();
        return mesh;
    }

    createTextLabel(mesh, text) {
        // Create canvas for text
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = 512;
        canvas.height = 256;

        // Draw text
        context.fillStyle = 'rgba(0, 0, 0, 0.8)';
        context.fillRect(0, 0, canvas.width, canvas.height);
        context.fillStyle = 'white';
        context.font = 'bold 40px Arial';
        context.textAlign = 'center';
        context.textBaseline = 'middle';

        // Word wrap
        const words = text.split(' ');
        const lines = [];
        let currentLine = words[0];

        for (let i = 1; i < words.length; i++) {
            const testLine = currentLine + ' ' + words[i];
            const metrics = context.measureText(testLine);
            if (metrics.width > canvas.width - 40) {
                lines.push(currentLine);
                currentLine = words[i];
            } else {
                currentLine = testLine;
            }
        }
        lines.push(currentLine);

        // Draw lines
        const lineHeight = 50;
        const startY = (canvas.height - lines.length * lineHeight) / 2 + lineHeight / 2;
        lines.forEach((line, i) => {
            context.fillText(line, canvas.width / 2, startY + i * lineHeight);
        });

        // Create sprite
        const texture = new THREE.CanvasTexture(canvas);
        const spriteMaterial = new THREE.SpriteMaterial({
            map: texture,
            transparent: true,
            opacity: 0.9
        });
        const sprite = new THREE.Sprite(spriteMaterial);
        sprite.scale.set(2, 1, 1);
        sprite.position.y = 0.8;

        // Remove old label if exists
        if (mesh.userData.label) {
            mesh.remove(mesh.userData.label);
        }

        mesh.add(sprite);
        mesh.userData.label = sprite;
    }

    updateObject(mesh, text, color, shape) {
        if (!mesh) return;

        // Update properties
        mesh.userData.text = text;
        mesh.userData.color = color;
        mesh.userData.shape = shape;

        // Update color
        mesh.material.color.setHex(color);

        // Update shape if different
        if (mesh.userData.shape !== shape) {
            const position = mesh.position.clone();
            const rotation = mesh.rotation.clone();
            const userData = mesh.userData;

            this.deleteObject(mesh);
            const newMesh = this.createObject(position, text, color, shape);
            newMesh.rotation.copy(rotation);
            newMesh.userData = { ...userData, shape: shape };
        } else {
            // Update text label
            this.createTextLabel(mesh, text);
        }

        this.saveToStorage();
    }

    deleteObject(mesh) {
        const index = this.objects.indexOf(mesh);
        if (index > -1) {
            this.objects.splice(index, 1);
        }

        if (mesh.userData.label) {
            mesh.remove(mesh.userData.label);
        }

        this.scene.remove(mesh);

        if (mesh.geometry) mesh.geometry.dispose();
        if (mesh.material) mesh.material.dispose();

        if (this.selectedObject === mesh) {
            this.selectedObject = null;
        }

        this.saveToStorage();
    }

    selectObject(mesh) {
        // Deselect previous
        if (this.selectedObject && this.selectedObject.userData.outline) {
            this.selectedObject.userData.outline.material.opacity = 0;
        }

        this.selectedObject = mesh;

        // Highlight selected
        if (mesh && mesh.userData.outline) {
            mesh.userData.outline.material.opacity = 0.5;
            mesh.userData.outline.material.color.setHex(0x00ff00);
        }
    }

    hoverObject(mesh) {
        // Remove previous hover
        if (this.hoveredObject &&
            this.hoveredObject !== this.selectedObject &&
            this.hoveredObject.userData.outline) {
            this.hoveredObject.userData.outline.material.opacity = 0;
        }

        this.hoveredObject = mesh;

        // Highlight hovered (if not selected)
        if (mesh &&
            mesh !== this.selectedObject &&
            mesh.userData.outline) {
            mesh.userData.outline.material.opacity = 0.3;
            mesh.userData.outline.material.color.setHex(0xffff00);
        }
    }

    update() {
        // Make objects slowly rotate
        this.objects.forEach(obj => {
            obj.rotation.y += 0.005;

            // Make label always face camera
            if (obj.userData.label) {
                obj.userData.label.rotation.y = -obj.rotation.y;
            }
        });
    }

    saveToStorage() {
        const data = this.objects.map(obj => ({
            position: {
                x: obj.position.x,
                y: obj.position.y,
                z: obj.position.z
            },
            rotation: {
                x: obj.rotation.x,
                y: obj.rotation.y,
                z: obj.rotation.z
            },
            text: obj.userData.text,
            color: obj.userData.color,
            shape: obj.userData.shape
        }));

        localStorage.setItem('memoryPalaceObjects', JSON.stringify(data));
        console.log('저장됨:', data.length, '개의 객체');
    }

    loadFromStorage() {
        const data = localStorage.getItem('memoryPalaceObjects');
        if (!data) return;

        try {
            const objects = JSON.parse(data);
            objects.forEach(objData => {
                const position = new THREE.Vector3(
                    objData.position.x,
                    objData.position.y,
                    objData.position.z
                );
                const mesh = this.createObject(
                    position,
                    objData.text,
                    objData.color,
                    objData.shape
                );
                mesh.rotation.set(
                    objData.rotation.x,
                    objData.rotation.y,
                    objData.rotation.z
                );
            });
            console.log('불러옴:', objects.length, '개의 객체');
        } catch (e) {
            console.error('객체 불러오기 실패:', e);
        }
    }

    clearAll() {
        while (this.objects.length > 0) {
            this.deleteObject(this.objects[0]);
        }
        this.saveToStorage();
    }

    generateId() {
        return 'obj_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    getObjectAt(point) {
        for (let obj of this.objects) {
            const distance = obj.position.distanceTo(point);
            if (distance < 0.5) {
                return obj;
            }
        }
        return null;
    }
}
