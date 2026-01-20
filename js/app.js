import MemoryPalace from './memoryPalace.js';
import ObjectManager from './objectManager.js';
import VRController from './vrController.js';

class MemoryPalaceVR {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.memoryPalace = null;
        this.objectManager = null;
        this.vrController = null;
        this.clock = new THREE.Clock();

        this.init();
    }

    init() {
        this.setupScene();
        this.setupVR();
        this.setupManagers();
        this.setupEventListeners();
        this.animate();
    }

    setupScene() {
        // Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x87ceeb);
        this.scene.fog = new THREE.Fog(0x87ceeb, 10, 50);

        // Camera
        this.camera = new THREE.PerspectiveCamera(
            75,
            window.innerWidth / window.innerHeight,
            0.1,
            1000
        );
        this.camera.position.set(0, 1.6, 3);

        // Renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.xr.enabled = true;
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        document.body.appendChild(this.renderer.domElement);

        // Lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(5, 10, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.camera.near = 0.1;
        directionalLight.shadow.camera.far = 50;
        directionalLight.shadow.camera.left = -10;
        directionalLight.shadow.camera.right = 10;
        directionalLight.shadow.camera.top = 10;
        directionalLight.shadow.camera.bottom = -10;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        this.scene.add(directionalLight);

        // Resize handler
        window.addEventListener('resize', () => {
            this.camera.aspect = window.innerWidth / window.innerHeight;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(window.innerWidth, window.innerHeight);
        });
    }

    setupVR() {
        // VR Button
        const vrButton = document.getElementById('vr-button');

        if ('xr' in navigator) {
            navigator.xr.isSessionSupported('immersive-vr').then((supported) => {
                if (supported) {
                    vrButton.disabled = false;
                    vrButton.textContent = 'VR 시작하기';
                    document.getElementById('status').textContent = 'VR 준비 완료!';
                } else {
                    document.getElementById('status').textContent = 'VR이 지원되지 않는 기기입니다';
                }
            });
        } else {
            document.getElementById('status').textContent = 'WebXR을 지원하지 않는 브라우저입니다';
        }

        vrButton.addEventListener('click', () => {
            if (!this.renderer.xr.isPresenting) {
                this.renderer.xr.getSession();
            }
        });

        this.renderer.xr.addEventListener('sessionstart', () => {
            document.getElementById('info').style.display = 'none';
            console.log('VR 세션 시작');
        });

        this.renderer.xr.addEventListener('sessionend', () => {
            document.getElementById('info').style.display = 'block';
            console.log('VR 세션 종료');
        });
    }

    setupManagers() {
        // Memory Palace
        this.memoryPalace = new MemoryPalace(this.scene);
        this.memoryPalace.create();

        // Object Manager
        this.objectManager = new ObjectManager(this.scene);
        this.objectManager.loadFromStorage();

        // VR Controller
        this.vrController = new VRController(
            this.renderer,
            this.scene,
            this.camera,
            this.objectManager
        );
    }

    setupEventListeners() {
        // UI Event Listeners
        document.getElementById('save-object').addEventListener('click', () => {
            const text = document.getElementById('object-text').value;
            const color = parseInt(document.getElementById('object-color').value);
            const shape = document.getElementById('object-shape').value;

            if (this.objectManager.selectedObject) {
                this.objectManager.updateObject(
                    this.objectManager.selectedObject,
                    text,
                    color,
                    shape
                );
            }

            document.getElementById('edit-panel').classList.add('hidden');
        });

        document.getElementById('cancel-edit').addEventListener('click', () => {
            document.getElementById('edit-panel').classList.add('hidden');
        });
    }

    animate() {
        this.renderer.setAnimationLoop(() => {
            const delta = this.clock.getDelta();

            if (this.vrController) {
                this.vrController.update(delta);
            }

            if (this.objectManager) {
                this.objectManager.update();
            }

            this.renderer.render(this.scene, this.camera);
        });
    }
}

// Initialize app
window.addEventListener('DOMContentLoaded', () => {
    new MemoryPalaceVR();
});
