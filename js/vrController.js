export default class VRController {
    constructor(renderer, scene, camera, objectManager) {
        this.renderer = renderer;
        this.scene = scene;
        this.camera = camera;
        this.objectManager = objectManager;

        this.controllers = [];
        this.raycaster = new THREE.Raycaster();
        this.tempMatrix = new THREE.Matrix4();
        this.moveSpeed = 3;
        this.rotateSpeed = 1.5;

        this.setupControllers();
        this.setupPlayerRig();
    }

    setupPlayerRig() {
        // Create player rig for movement
        this.playerRig = new THREE.Group();
        this.playerRig.position.set(0, 0, 0);
        this.scene.add(this.playerRig);
        this.playerRig.add(this.camera);
    }

    setupControllers() {
        // Controller 0 (left)
        const controller0 = this.renderer.xr.getController(0);
        controller0.addEventListener('selectstart', () => this.onSelectStart(0));
        controller0.addEventListener('selectend', () => this.onSelectEnd(0));
        this.playerRig ? this.playerRig.add(controller0) : this.scene.add(controller0);

        // Controller 1 (right)
        const controller1 = this.renderer.xr.getController(1);
        controller1.addEventListener('selectstart', () => this.onSelectStart(1));
        controller1.addEventListener('selectend', () => this.onSelectEnd(1));
        this.playerRig ? this.playerRig.add(controller1) : this.scene.add(controller1);

        // Add visual representation
        const geometry = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(0, 0, 0),
            new THREE.Vector3(0, 0, -1)
        ]);
        const material = new THREE.LineBasicMaterial({ color: 0x00ff00 });

        const line0 = new THREE.Line(geometry, material);
        controller0.add(line0);

        const line1 = new THREE.Line(geometry, material);
        controller1.add(line1);

        // Controller grips
        const controllerGrip0 = this.renderer.xr.getControllerGrip(0);
        this.playerRig ? this.playerRig.add(controllerGrip0) : this.scene.add(controllerGrip0);

        const controllerGrip1 = this.renderer.xr.getControllerGrip(1);
        this.playerRig ? this.playerRig.add(controllerGrip1) : this.scene.add(controllerGrip1);

        // Add controller models
        const controllerModelFactory = new THREE.XRControllerModelFactory();
        if (typeof controllerModelFactory.createControllerModel === 'function') {
            controllerGrip0.add(controllerModelFactory.createControllerModel(controllerGrip0));
            controllerGrip1.add(controllerModelFactory.createControllerModel(controllerGrip1));
        }

        this.controllers = [
            { controller: controller0, grip: controllerGrip0, line: line0 },
            { controller: controller1, grip: controllerGrip1, line: line1 }
        ];
    }

    onSelectStart(index) {
        const controller = this.controllers[index];

        if (index === 1) {
            // Right controller: Create object
            this.createObjectAtController(controller.controller);
        } else {
            // Left controller: Select object
            this.selectObjectAtController(controller.controller);
        }
    }

    onSelectEnd(index) {
        // Handle select end if needed
    }

    createObjectAtController(controller) {
        this.tempMatrix.identity().extractRotation(controller.matrixWorld);

        const position = new THREE.Vector3();
        position.setFromMatrixPosition(controller.matrixWorld);
        position.add(new THREE.Vector3(0, 0, -1).applyMatrix4(this.tempMatrix));
        position.y = Math.max(position.y, 1.2); // Keep above pedestals

        this.objectManager.createObject(position);
        console.log('객체 생성됨');
    }

    selectObjectAtController(controller) {
        this.raycaster.ray.origin.setFromMatrixPosition(controller.matrixWorld);
        this.tempMatrix.identity().extractRotation(controller.matrixWorld);
        this.raycaster.ray.direction.set(0, 0, -1).applyMatrix4(this.tempMatrix);

        const intersects = this.raycaster.intersectObjects(this.objectManager.objects);

        if (intersects.length > 0) {
            const selectedObj = intersects[0].object;
            this.objectManager.selectObject(selectedObj);
            console.log('객체 선택됨:', selectedObj.userData.text);

            // Show edit panel
            this.showEditPanel(selectedObj);
        }
    }

    showEditPanel(obj) {
        const panel = document.getElementById('edit-panel');
        document.getElementById('object-text').value = obj.userData.text;
        document.getElementById('object-color').value = '0x' + obj.userData.color.toString(16).padStart(6, '0');
        document.getElementById('object-shape').value = obj.userData.shape;
        panel.classList.remove('hidden');
    }

    update(delta) {
        if (!this.renderer.xr.isPresenting) return;

        const session = this.renderer.xr.getSession();
        if (!session) return;

        // Get gamepad inputs
        for (let i = 0; i < session.inputSources.length; i++) {
            const inputSource = session.inputSources[i];
            const gamepad = inputSource.gamepad;

            if (gamepad && gamepad.axes.length >= 4) {
                if (inputSource.handedness === 'left') {
                    // Left controller: Movement
                    const x = gamepad.axes[2];
                    const z = gamepad.axes[3];

                    if (Math.abs(x) > 0.1 || Math.abs(z) > 0.1) {
                        const moveVector = new THREE.Vector3(x, 0, z);
                        moveVector.applyQuaternion(this.camera.quaternion);
                        moveVector.y = 0;
                        moveVector.normalize();
                        moveVector.multiplyScalar(this.moveSpeed * delta);

                        this.playerRig.position.add(moveVector);
                    }
                } else if (inputSource.handedness === 'right') {
                    // Right controller: Rotation
                    const rotateX = gamepad.axes[2];

                    if (Math.abs(rotateX) > 0.1) {
                        this.playerRig.rotation.y -= rotateX * this.rotateSpeed * delta;
                    }
                }

                // Button handling
                if (gamepad.buttons.length > 0) {
                    // B button (button 1): Delete selected object
                    if (gamepad.buttons[1] && gamepad.buttons[1].pressed) {
                        if (this.objectManager.selectedObject && !this.deletePressed) {
                            this.objectManager.deleteObject(this.objectManager.selectedObject);
                            console.log('객체 삭제됨');
                            this.deletePressed = true;
                        }
                    } else {
                        this.deletePressed = false;
                    }

                    // Y button (button 3): Save
                    if (gamepad.buttons[3] && gamepad.buttons[3].pressed) {
                        if (!this.savePressed) {
                            this.objectManager.saveToStorage();
                            console.log('저장됨');
                            this.savePressed = true;
                        }
                    } else {
                        this.savePressed = false;
                    }
                }
            }
        }

        // Update controller rays
        this.updateRays();
    }

    updateRays() {
        this.controllers.forEach((ctrl, index) => {
            this.raycaster.ray.origin.setFromMatrixPosition(ctrl.controller.matrixWorld);
            this.tempMatrix.identity().extractRotation(ctrl.controller.matrixWorld);
            this.raycaster.ray.direction.set(0, 0, -1).applyMatrix4(this.tempMatrix);

            const intersects = this.raycaster.intersectObjects(this.objectManager.objects);

            if (intersects.length > 0) {
                const distance = intersects[0].distance;
                ctrl.line.scale.z = distance;
                ctrl.line.material.color.setHex(0xff0000);

                // Hover effect
                if (index === 0) { // Left controller
                    this.objectManager.hoverObject(intersects[0].object);
                }
            } else {
                ctrl.line.scale.z = 5;
                ctrl.line.material.color.setHex(0x00ff00);

                if (index === 0) {
                    this.objectManager.hoverObject(null);
                }
            }
        });
    }
}

// XRControllerModelFactory polyfill for older Three.js versions
if (typeof THREE.XRControllerModelFactory === 'undefined') {
    THREE.XRControllerModelFactory = class {
        createControllerModel() {
            // Simple controller representation
            const geometry = new THREE.BoxGeometry(0.05, 0.05, 0.15);
            const material = new THREE.MeshStandardMaterial({ color: 0x333333 });
            return new THREE.Mesh(geometry, material);
        }
    };
}
