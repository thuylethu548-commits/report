/**
 * ASTRA QUANT 3D DIGITAL TWIN WORLD ENGINE (CHUẨN TELLUX & HIGH-END WEBGIS)
 * High-End 3D WebGL Metaverse for Astra Quant Fleet:
 * - Rayleigh/Mie Atmospheric Scattering Sky Dome
 * - PBR Reflective Citadel Floor & 10 Spatial Agent Holographic Pods
 * - Live Vector Field Particle Flows (Tellux Wind3D)
 * - 3D Billboard Speech Bubbles & Raycast Interaction
 * - Cinematic Drone Flyover & Tactical Orbit Controls
 */

class Astra3DWorldEngine {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`[3D World] Container #${containerId} not found!`);
            return;
        }

        this.options = options;
        this.isMobile = window.innerWidth < 768;
        
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.clock = new THREE.Clock();
        
        this.agentPods = {};
        this.speechBubbles = {};
        this.vectorField = null;
        
        this.cameraMode = 'ORBIT'; // 'ORBIT', 'FLYOVER', 'FOCUS'
        this.flyoverAngle = 0.0;
        this.targetCameraPos = null;
        this.targetLookAt = null;
        
        // GIS Cockpit Telemetry
        this.fps = 60;
        this.frameCount = 0;
        this.lastFpsUpdate = performance.now();
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        this.hoveredPod = null;

        // Physical Cyber-Infrastructure Subsystems
        this.infraGroup = null;
        this.powerGroup = null;
        this.fiberGroup = null;
        this.telecomGroup = null;
        this.serverGroup = null;

        this.powerConduits = [];
        this.powerSparks = [];
        this.fiberCurves = [];
        this.fiberPackets = [];
        this.serverFans = [];
        this.serverLeds = [];
        this.wifiRipples = [];
        this.microwaveBeam = null;
        this.layerVisibility = { power: true, fiber: true, server: true, telecom: true };

        // Visual Presets
        this.presets = {
            CYBERPUNK: {
                skyTop: 0x050814,
                skyHorizon: 0x0d213a,
                sunColor: 0x38bdf8,
                ambient: 0x0a1628,
                fogDensity: 0.003
            },
            SUNSET: {
                skyTop: 0x180b26,
                skyHorizon: 0xf59e0b,
                sunColor: 0xfb923c,
                ambient: 0x1f1424,
                fogDensity: 0.0035
            },
            MATRIX: {
                skyTop: 0x02130b,
                skyHorizon: 0x052e16,
                sunColor: 0x10b981,
                ambient: 0x041f10,
                fogDensity: 0.004
            }
        };
        this.currentPreset = 'CYBERPUNK';

        // 3D Autonomous RPG Gameplay Simulation (GPT-5 / GTA-V Style)
        this.humanoids = {};
        this.rpgWaypoints = {
            centerHub: new THREE.Vector3(0, 0, 0),
            coffeeBar: new THREE.Vector3(0, 0, 105),
            serverRoom: new THREE.Vector3(-105, 0, 0),
            telecomDeck: new THREE.Vector3(105, 0, 0)
        };
        this.rpgState = {
            alarmActive: false,
            alarmTime: 0,
            partyMode: false
        };
        this.agentLessonDialogues = {
            "Palermo": [
                "EMA-20/50 đang dốc lên mạnh, phe Long nắm quyền chủ động!",
                "Đòn lỳ 10U của Boss: gồng lãi theo đúng target kháng cự.",
                "Thị trường sóng khỏe, hạn chế nhảy ra nhảy vào mất vị thế."
            ],
            "Rik": [
                "Cảnh sát rủi ro: Hard Risk Gate 2% bảo vệ vốn tuyệt đối!",
                "Tuyệt đối không giao dịch P2P ngoài sàn, đề phòng bẫy đóng băng bank!",
                "Mọi lệnh đều phải có Stop-Loss cứng, không gồng lỗ vô lý."
            ],
            "Prof": [
                "CVaR 5D Tensor đạt độ tin cậy 98.4%, Kalman Filter khử nhiễu.",
                "Tránh bẫy đòn bẩy 50X: Phí funding rate sẽ bào mòn tài khoản.",
                "Vector thanh khoản đang hội tụ tại vùng giá $81,200."
            ],
            "Tory": [
                "Dải Donchian 20 nén chặt, chuẩn bị xuất hiện breakout cực mạnh!",
                "Khối lượng volume xác nhận vượt trung bình 20 ngày."
            ],
            "Hash": [
                "Ví cá voi vừa nạp ròng 1,200 BTC, tâm lý On-Chain tích cực.",
                "Bảo mật tài sản: Sàn CEX để trade, lợi nhuận lớn rút về Ledger."
            ],
            "Meme": [
                "Khớp lệnh trực tiếp qua OMS Bunker, độ trễ chỉ 74ms.",
                "Sổ lệnh L2 có tường mua 450 BTC bảo vệ mốc hỗ trợ."
            ],
            "Deck": [
                "Spread sàn CEX-DEX chênh 0.04%, kích hoạt Arbitrage phi rủi ro.",
                "Funding Rate dương cao: Cảnh báo Long squeeze trước khi đảo chiều."
            ],
            "Volt": [
                "Biến động Gaussian σ đang hạ nhiệt, vùng tích lũy hình thành.",
                "Dải Bollinger mở rộng 2 đầu: Chuẩn bị có sóng lớn quét thanh khoản."
            ],
            "Core": [
                "Đã lưu trữ 37 bài học xương máu vào SQLite trading_bot.db.",
                "Chiến thuật Free-Roll: X2 rút toàn bộ gốc, chỉ để lãi chạy!",
                "High-Water Mark tài khoản đạt đỉnh mới, tỷ lệ Sharpe 1.42."
            ],
            "Sniper": [
                "Chiến lược tích lũy Spot DCA 500U: Mua khi thị trường chiết khấu sâu 80-83k.",
                "Giữ két sắt 450U Vault ngoài sàn Futures, không bao giờ tất tay vào phái sinh!",
                "Kiên nhẫn gom coin nền tảng BTC/ETH/SOL, không fomo đỉnh."
            ],
            "Square": [
                "Đã phát tín hiệu minh bạch lên Binance Square & Telegram Pro.",
                "Cộng đồng theo dõi chặt chẽ từng nhịp thở của Hội đồng 12 Tác Tử.",
                "Lắng nghe phản hồi thị trường để tối ưu hóa trải nghiệm nhà đầu tư."
            ],
            "Astra": [
                "Hội đồng 12 AI Agents đồng thuận cao: Phê duyệt tín hiệu vào lệnh.",
                "Tổng Quản Tối Cao giám sát 24/7, luôn đồng hành cùng Boss!",
                "Kỷ luật định lượng là chìa khóa duy nhất để chiến thắng thị trường."
            ]
        };

        this.init();
    }

    init() {
        const width = this.container.clientWidth || window.innerWidth;
        const height = this.container.clientHeight || 550;

        // 1. Scene & Atmosphere
        this.scene = new THREE.Scene();
        this.scene.fog = new THREE.FogExp2(0x060b18, this.presets.CYBERPUNK.fogDensity);

        // 2. Camera
        this.camera = new THREE.PerspectiveCamera(52, width / height, 0.5, 2500);
        this.camera.position.set(0, 110, 175);

        // 3. Renderer
        this.renderer = new THREE.WebGLRenderer({
            antialias: !this.isMobile,
            alpha: true,
            powerPreference: 'high-performance'
        });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2.0));
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.15;
        this.renderer.shadowMap.enabled = !this.isMobile;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        
        this.container.innerHTML = '';
        this.container.appendChild(this.renderer.domElement);

        // 4. OrbitControls
        if (typeof THREE.OrbitControls !== 'undefined') {
            this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.06;
            this.controls.maxPolarAngle = Math.PI / 2.08;
            this.controls.minDistance = 25;
            this.controls.maxDistance = 420;
            this.controls.target.set(0, 8, 0);
        }

        // 5. Build Environment & Geometry
        this.createAtmosphericSky();
        this.createLighting();
        this.createCitadelFloor();
        this.createCentralQuantumCore();
        this.createCentralWarRoomTable();
        this.createCoffeeLoungeLandmark();
        this.createAgentPods();
        this.createPhysicalInfrastructure();

        // 6. Vector Field Particle Streamlines (Tellux Wind3D inspired)
        if (typeof LiquidityVectorField !== 'undefined') {
            this.vectorField = new LiquidityVectorField(this.scene, {
                particleCount: this.isMobile ? 1200 : 3200
            });
        }

        // 7. Event Listeners
        window.addEventListener('resize', () => this.onWindowResize());
        this.renderer.domElement.addEventListener('mousemove', (e) => this.onPointerMove(e));
        this.renderer.domElement.addEventListener('click', (e) => this.onPointerClick(e));
        this.renderer.domElement.addEventListener('touchstart', (e) => this.onTouchStart(e), { passive: true });

        // 8. Start Render Loop
        this.animate();
        console.log("[3D World] Astra Digital Twin World Engine initialized successfully!");
    }

    createAtmosphericSky() {
        // High-end Atmospheric Sky Dome with Rayleigh/Mie gradient simulation
        const vertexShader = `
            varying vec3 vWorldPosition;
            void main() {
                vec4 worldPosition = modelMatrix * vec4(position, 1.0);
                vWorldPosition = worldPosition.xyz;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `;

        const fragmentShader = `
            uniform vec3 topColor;
            uniform vec3 bottomColor;
            uniform float offset;
            uniform float exponent;
            varying vec3 vWorldPosition;
            void main() {
                float h = normalize(vWorldPosition + offset).y;
                gl_FragColor = vec4(mix(bottomColor, topColor, max(pow(max(h, 0.0), exponent), 0.0)), 1.0);
            }
        `;

        const uniforms = {
            topColor: { value: new THREE.Color(this.presets[this.currentPreset].skyTop) },
            bottomColor: { value: new THREE.Color(this.presets[this.currentPreset].skyHorizon) },
            offset: { value: 33 },
            exponent: { value: 0.6 }
        };

        const skyGeo = new THREE.SphereGeometry(1200, 32, 15);
        this.skyMat = new THREE.ShaderMaterial({
            vertexShader,
            fragmentShader,
            uniforms,
            side: THREE.BackSide,
            depthWrite: false
        });

        this.skyDome = new THREE.Mesh(skyGeo, this.skyMat);
        this.scene.add(this.skyDome);

        // Add subtle cosmic starfield particles
        const starGeo = new THREE.BufferGeometry();
        const starCount = this.isMobile ? 500 : 1500;
        const starPositions = new Float32Array(starCount * 3);
        for (let i = 0; i < starCount * 3; i += 3) {
            const u = Math.random();
            const v = Math.random();
            const theta = u * 2.0 * Math.PI;
            const phi = Math.acos(2.0 * v - 1.0);
            const r = 900 + Math.random() * 200;
            starPositions[i] = r * Math.sin(phi) * Math.cos(theta);
            starPositions[i + 1] = Math.abs(r * Math.cos(phi));
            starPositions[i + 2] = r * Math.sin(phi) * Math.sin(theta);
        }
        starGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
        const starMat = new THREE.PointsMaterial({
            color: 0x94a3b8,
            size: 2.0,
            transparent: true,
            opacity: 0.75,
            depthWrite: false
        });
        this.stars = new THREE.Points(starGeo, starMat);
        this.scene.add(this.stars);
    }

    createLighting() {
        // Celestial Sun / Directional Light with soft shadows
        this.sunLight = new THREE.DirectionalLight(0x38bdf8, 1.4);
        this.sunLight.position.set(80, 160, 100);
        this.sunLight.castShadow = !this.isMobile;
        if (this.sunLight.castShadow) {
            this.sunLight.shadow.mapSize.width = 1024;
            this.sunLight.shadow.mapSize.height = 1024;
            this.sunLight.shadow.camera.near = 10;
            this.sunLight.shadow.camera.far = 400;
            this.sunLight.shadow.camera.left = -150;
            this.sunLight.shadow.camera.right = 150;
            this.sunLight.shadow.camera.top = 150;
            this.sunLight.shadow.camera.bottom = -150;
            this.sunLight.shadow.bias = -0.0005;
        }
        this.scene.add(this.sunLight);

        // Cyber Ambient Glow
        this.ambientLight = new THREE.AmbientLight(0x0f172a, 1.8);
        this.scene.add(this.ambientLight);

        // Core Quantum Uplight (from below ground)
        const coreLight = new THREE.PointLight(0xa855f7, 2.5, 90);
        coreLight.position.set(0, 15, 0);
        this.scene.add(coreLight);
    }

    createCitadelFloor() {
        // 1. PBR Floor Platform
        const floorGeo = new THREE.CylinderGeometry(145, 155, 4, 48);
        const floorMat = new THREE.MeshStandardMaterial({
            color: 0x0b1120,
            roughness: 0.25,
            metalness: 0.85,
            flatShading: false
        });
        this.floorMesh = new THREE.Mesh(floorGeo, floorMat);
        this.floorMesh.position.y = -2;
        this.floorMesh.receiveShadow = true;
        this.scene.add(this.floorMesh);

        // 2. Futuristic Grid & Circuit Overlay
        const gridHelper = new THREE.GridHelper(260, 36, 0x0284c7, 0x1e293b);
        gridHelper.position.y = 0.05;
        this.scene.add(gridHelper);

        // 3. Concentric Cyber Energy Rings on the floor
        const ringGeo1 = new THREE.RingGeometry(138, 142, 64);
        const ringMat1 = new THREE.MeshBasicMaterial({
            color: 0x38bdf8,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.65
        });
        const outerRing = new THREE.Mesh(ringGeo1, ringMat1);
        outerRing.rotation.x = -Math.PI / 2;
        outerRing.position.y = 0.1;
        this.scene.add(outerRing);

        const ringGeo2 = new THREE.RingGeometry(42, 44, 48);
        const ringMat2 = new THREE.MeshBasicMaterial({
            color: 0xa855f7,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.75
        });
        const innerRing = new THREE.Mesh(ringGeo2, ringMat2);
        innerRing.rotation.x = -Math.PI / 2;
        innerRing.position.y = 0.12;
        this.scene.add(innerRing);
    }

    createCentralQuantumCore() {
        // 5D Quantum Confluence Core (Supreme Spire)
        this.quantumCoreGroup = new THREE.Group();
        this.quantumCoreGroup.position.set(0, 16, 0);

        // Floating pulsating Icosahedron
        const icoGeo = new THREE.IcosahedronGeometry(7.5, 1);
        const icoMat = new THREE.MeshStandardMaterial({
            color: 0x8b5cf6,
            emissive: 0x6d28d9,
            emissiveIntensity: 0.8,
            roughness: 0.15,
            metalness: 0.9,
            wireframe: false,
            transparent: true,
            opacity: 0.88
        });
        this.coreMesh = new THREE.Mesh(icoGeo, icoMat);
        this.coreMesh.castShadow = true;
        this.quantumCoreGroup.add(this.coreMesh);

        // Wireframe holographic shell
        const wireMat = new THREE.MeshBasicMaterial({
            color: 0x38bdf8,
            wireframe: true,
            transparent: true,
            opacity: 0.4
        });
        const wireMesh = new THREE.Mesh(new THREE.IcosahedronGeometry(9.0, 1), wireMat);
        this.quantumCoreGroup.add(wireMesh);
        this.wireMesh = wireMesh;

        // Dual Spinning Energy Rings around core
        const torusGeo1 = new THREE.TorusGeometry(12, 0.4, 16, 64);
        const torusMat1 = new THREE.MeshBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.8 });
        this.torus1 = new THREE.Mesh(torusGeo1, torusMat1);
        this.quantumCoreGroup.add(this.torus1);

        const torusGeo2 = new THREE.TorusGeometry(14, 0.3, 16, 64);
        const torusMat2 = new THREE.MeshBasicMaterial({ color: 0xa855f7, transparent: true, opacity: 0.6 });
        this.torus2 = new THREE.Mesh(torusGeo2, torusMat2);
        this.torus2.rotation.x = Math.PI / 3;
        this.quantumCoreGroup.add(this.torus2);

        // Floating Billboard Tag for Quantum Core
        const tag = this.createBillboardText("5D QUANTUM TENSOR CORE", "Astra Supreme Orchestrator", "#a855f7");
        tag.position.set(0, 16, 0);
        this.quantumCoreGroup.add(tag);

        this.scene.add(this.quantumCoreGroup);
    }

    toggleQuantum3dCore(forceVisible) {
        if (!this.quantumCoreGroup) return false;
        if (typeof forceVisible === 'boolean') {
            this.quantumCoreGroup.visible = forceVisible;
        } else {
            this.quantumCoreGroup.visible = !this.quantumCoreGroup.visible;
        }
        return this.quantumCoreGroup.visible;
    }

    createCentralWarRoomTable() {
        const warRoom = new THREE.Group();
        warRoom.position.set(0, 0, 0);

        // 1. Circular Hologram Console Table
        const tableGeo = new THREE.CylinderGeometry(14, 16, 2.2, 32);
        const tableMat = new THREE.MeshStandardMaterial({
            color: 0x0f172a,
            roughness: 0.2,
            metalness: 0.9
        });
        const tableMesh = new THREE.Mesh(tableGeo, tableMat);
        tableMesh.position.y = 1.1;
        tableMesh.receiveShadow = true;
        warRoom.add(tableMesh);

        // 2. Glowing Holographic Top Disk
        const topGeo = new THREE.CylinderGeometry(13.2, 13.2, 0.2, 32);
        const topMat = new THREE.MeshBasicMaterial({
            color: 0x38bdf8,
            transparent: true,
            opacity: 0.75
        });
        const topMesh = new THREE.Mesh(topGeo, topMat);
        topMesh.position.y = 2.25;
        warRoom.add(topMesh);

        // 3. Mini Holographic Candlestick Ring around center
        const candleGroup = new THREE.Group();
        candleGroup.position.y = 4.5;
        for (let i = 0; i < 16; i++) {
            const angle = (i / 16) * Math.PI * 2;
            const r = 9.5;
            const isGreen = i % 3 !== 0;
            const h = 1.5 + Math.sin(i * 1.5) * 1.0;
            const candleGeo = new THREE.BoxGeometry(0.6, h, 0.6);
            const candleMat = new THREE.MeshBasicMaterial({
                color: isGreen ? 0x10b981 : 0xef4444,
                transparent: true,
                opacity: 0.85
            });
            const candle = new THREE.Mesh(candleGeo, candleMat);
            candle.position.set(Math.cos(angle) * r, h / 2, Math.sin(angle) * r);
            candleGroup.add(candle);
        }
        warRoom.add(candleGroup);
        this.warRoomCandles = candleGroup;

        // 4. Strategic Label
        const label = this.createBillboardText("WAR ROOM TỐI CAO", "Bàn Tranh Biện 10 Tác Tử · Gated AI", "#38bdf8");
        label.position.set(0, 11, 0);
        warRoom.add(label);

        this.scene.add(warRoom);
        this.warRoomGroup = warRoom;
    }

    createCoffeeLoungeLandmark() {
        const lounge = new THREE.Group();
        lounge.position.set(0, 0, 105);

        // 1. Deck Platform
        const deckGeo = new THREE.BoxGeometry(36, 1.4, 24);
        const deckMat = new THREE.MeshStandardMaterial({
            color: 0x18181b,
            roughness: 0.6,
            metalness: 0.3
        });
        const deck = new THREE.Mesh(deckGeo, deckMat);
        deck.position.y = 0.7;
        deck.receiveShadow = true;
        lounge.add(deck);

        // 2. Glowing Amber Border Trim
        const borderGeo = new THREE.BoxGeometry(36.4, 0.4, 24.4);
        const borderMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b });
        const border = new THREE.Mesh(borderGeo, borderMat);
        border.position.y = 1.3;
        lounge.add(border);

        // 3. Cyber Espresso Bar Counter
        const barGeo = new THREE.BoxGeometry(18, 4.0, 4);
        const barMat = new THREE.MeshStandardMaterial({ color: 0x27272a, metalness: 0.8 });
        const bar = new THREE.Mesh(barGeo, barMat);
        bar.position.set(0, 2.7, -4);
        lounge.add(bar);

        // Espresso Machine
        const machineGeo = new THREE.BoxGeometry(4, 2.2, 2.5);
        const machineMat = new THREE.MeshStandardMaterial({ color: 0xd97706, metalness: 0.9 });
        const machine = new THREE.Mesh(machineGeo, machineMat);
        machine.position.set(-4, 5.8, -4);
        lounge.add(machine);

        // 4. Neon Sign Billboard
        const neonSign = this.createBillboardText("☕ ASTRA COFFEE LOUNGE", "Khu Nghỉ Ngơi & Đàm Thoại 10 Tác Tử", "#f59e0b");
        neonSign.position.set(0, 10.5, -4);
        lounge.add(neonSign);

        // Warm Lounge Point Light
        const loungeLight = new THREE.PointLight(0xf59e0b, 1.8, 45);
        loungeLight.position.set(0, 7, 0);
        lounge.add(loungeLight);

        this.scene.add(lounge);
        this.coffeeLounge = lounge;
    }

    buildHumanoidCharacter(ag) {
        const charGroup = new THREE.Group();
        charGroup.name = `humanoid_${ag.name}`;

        const skinMat = new THREE.MeshStandardMaterial({
            color: 0xffdfc4,
            roughness: 0.6,
            metalness: 0.1
        });

        const suitMat = new THREE.MeshStandardMaterial({
            color: 0x0f172a,
            roughness: 0.4,
            metalness: 0.6
        });

        const trimMat = new THREE.MeshStandardMaterial({
            color: ag.hex,
            emissive: ag.hex,
            emissiveIntensity: 0.65,
            roughness: 0.2,
            metalness: 0.8
        });

        const visorMat = new THREE.MeshStandardMaterial({
            color: ag.hex,
            emissive: ag.hex,
            emissiveIntensity: 0.95,
            roughness: 0.1,
            metalness: 0.9,
            transparent: true,
            opacity: 0.92
        });

        // 1. Pelvis / Hips (Root of body)
        const pelvisGeo = new THREE.BoxGeometry(2.4, 1.2, 1.6);
        const pelvis = new THREE.Mesh(pelvisGeo, suitMat);
        pelvis.position.y = 5.2;
        charGroup.add(pelvis);

        // 2. Torso / Tactical Jacket
        const torsoGeo = new THREE.BoxGeometry(2.8, 3.2, 1.8);
        const torso = new THREE.Mesh(torsoGeo, suitMat);
        torso.position.y = 2.2;
        pelvis.add(torso);

        // Departmental Armor Chest Plate
        const chestGeo = new THREE.BoxGeometry(2.0, 1.8, 0.35);
        const chest = new THREE.Mesh(chestGeo, trimMat);
        chest.position.set(0, 0.4, 0.95);
        torso.add(chest);

        // 3. Neck & Head
        const neckGeo = new THREE.CylinderGeometry(0.5, 0.6, 0.6, 8);
        const neck = new THREE.Mesh(neckGeo, skinMat);
        neck.position.y = 1.9;
        torso.add(neck);

        const headGroup = new THREE.Group();
        headGroup.position.y = 1.0;
        neck.add(headGroup);

        const headGeo = new THREE.BoxGeometry(1.8, 2.0, 1.8);
        const head = new THREE.Mesh(headGeo, skinMat);
        headGroup.add(head);

        const capGeo = new THREE.BoxGeometry(1.9, 0.8, 1.9);
        const cap = new THREE.Mesh(capGeo, suitMat);
        cap.position.y = 0.8;
        headGroup.add(cap);

        const visorGeo = new THREE.BoxGeometry(1.7, 0.5, 0.4);
        const visor = new THREE.Mesh(visorGeo, visorMat);
        visor.position.set(0, 0.15, 0.95);
        headGroup.add(visor);

        const headsetGeo = new THREE.BoxGeometry(2.1, 0.4, 0.5);
        const headset = new THREE.Mesh(headsetGeo, trimMat);
        headset.position.set(0, 0.2, 0);
        headGroup.add(headset);

        // 4. Arms (Hierarchical Shoulder -> Elbow -> Hand)
        // Left Arm
        const leftArm = new THREE.Group();
        leftArm.position.set(1.8, 1.2, 0);
        torso.add(leftArm);
        const lUpper = new THREE.Mesh(new THREE.BoxGeometry(0.8, 1.6, 0.8), suitMat);
        lUpper.position.y = -0.8;
        leftArm.add(lUpper);

        const leftForearm = new THREE.Group();
        leftForearm.position.y = -1.6;
        leftArm.add(leftForearm);
        const lFore = new THREE.Mesh(new THREE.BoxGeometry(0.7, 1.5, 0.7), suitMat);
        lFore.position.y = -0.75;
        leftForearm.add(lFore);
        const lHand = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.6, 0.5), skinMat);
        lHand.position.y = -1.6;
        leftForearm.add(lHand);

        // Right Arm
        const rightArm = new THREE.Group();
        rightArm.position.set(-1.8, 1.2, 0);
        torso.add(rightArm);
        const rUpper = new THREE.Mesh(new THREE.BoxGeometry(0.8, 1.6, 0.8), suitMat);
        rUpper.position.y = -0.8;
        rightArm.add(rUpper);

        const rightForearm = new THREE.Group();
        rightForearm.position.y = -1.6;
        rightArm.add(rightForearm);
        const rFore = new THREE.Mesh(new THREE.BoxGeometry(0.7, 1.5, 0.7), suitMat);
        rFore.position.y = -0.75;
        rightForearm.add(rFore);
        const rHand = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.6, 0.5), skinMat);
        rHand.position.y = -1.6;
        rightForearm.add(rHand);

        // 5. Legs (Hip -> Knee -> Boot)
        // Left Leg
        const leftLeg = new THREE.Group();
        leftLeg.position.set(0.7, -0.6, 0);
        pelvis.add(leftLeg);
        const lThigh = new THREE.Mesh(new THREE.BoxGeometry(0.9, 2.2, 0.9), suitMat);
        lThigh.position.y = -1.1;
        leftLeg.add(lThigh);

        const leftCalf = new THREE.Group();
        leftCalf.position.y = -2.2;
        leftLeg.add(leftCalf);
        const lCalf = new THREE.Mesh(new THREE.BoxGeometry(0.8, 2.0, 0.8), suitMat);
        lCalf.position.y = -1.0;
        leftCalf.add(lCalf);
        const lBoot = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.8, 1.4), trimMat);
        lBoot.position.set(0, -2.1, 0.25);
        leftCalf.add(lBoot);

        // Right Leg
        const rightLeg = new THREE.Group();
        rightLeg.position.set(-0.7, -0.6, 0);
        pelvis.add(rightLeg);
        const rThigh = new THREE.Mesh(new THREE.BoxGeometry(0.9, 2.2, 0.9), suitMat);
        rThigh.position.y = -1.1;
        rightLeg.add(rThigh);

        const rightCalf = new THREE.Group();
        rightCalf.position.y = -2.2;
        rightLeg.add(rightCalf);
        const rCalf = new THREE.Mesh(new THREE.BoxGeometry(0.8, 2.0, 0.8), suitMat);
        rCalf.position.y = -1.0;
        rightCalf.add(rCalf);
        const rBoot = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.8, 1.4), trimMat);
        rBoot.position.set(0, -2.1, 0.25);
        rightCalf.add(rBoot);

        // Store bones for procedural animation
        charGroup.bones = {
            pelvis,
            torso,
            headGroup,
            leftArm,
            rightArm,
            leftForearm,
            rightForearm,
            leftLeg,
            rightLeg,
            leftCalf,
            rightCalf
        };

        return charGroup;
    }

    buildWorkstationDesk(ag) {
        const deskGroup = new THREE.Group();

        // 1. Sleek Modern Trading Desk Top
        const deskTopGeo = new THREE.BoxGeometry(10, 0.4, 5.5);
        const deskTopMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.3, metalness: 0.8 });
        const deskTop = new THREE.Mesh(deskTopGeo, deskTopMat);
        deskTop.position.set(0, 3.8, 2.0);
        deskGroup.add(deskTop);

        // Dual Metallic Legs
        [-4.2, 4.2].forEach(xOff => {
            const legGeo = new THREE.BoxGeometry(0.6, 3.8, 4.8);
            const legMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.9 });
            const leg = new THREE.Mesh(legGeo, legMat);
            leg.position.set(xOff, 1.9, 2.0);
            deskGroup.add(leg);
        });

        // 2. Triple Holographic Curved Trading Monitors
        const monMat = new THREE.MeshStandardMaterial({
            color: 0x0284c7,
            emissive: ag.hex,
            emissiveIntensity: 0.5,
            roughness: 0.1,
            metalness: 0.85
        });

        const centerMon = new THREE.Mesh(new THREE.BoxGeometry(4.2, 2.4, 0.15), monMat);
        centerMon.position.set(0, 5.6, 3.2);
        deskGroup.add(centerMon);

        const leftMon = new THREE.Mesh(new THREE.BoxGeometry(3.2, 2.2, 0.15), monMat);
        leftMon.position.set(-3.6, 5.5, 2.8);
        leftMon.rotation.y = 0.45;
        deskGroup.add(leftMon);

        const rightMon = new THREE.Mesh(new THREE.BoxGeometry(3.2, 2.2, 0.15), monMat);
        rightMon.position.set(3.6, 5.5, 2.8);
        rightMon.rotation.y = -0.45;
        deskGroup.add(rightMon);

        // 3. Ergonomic Office Chair
        const chairMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.7 });
        const chairSeat = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.4, 2.4), chairMat);
        chairSeat.position.set(0, 2.6, -1.8);
        deskGroup.add(chairSeat);

        const chairBack = new THREE.Mesh(new THREE.BoxGeometry(2.4, 3.2, 0.4), chairMat);
        chairBack.position.set(0, 4.2, -2.9);
        deskGroup.add(chairBack);

        return deskGroup;
    }

    createAgentPods() {
        // Agent metadata matching SpatialAgentBrain 3D coordinates & styles (Hội đồng 12 Tác Tử)
        const AGENTS = [
            { name: "Astra", title: "Tổng Quản Tối Cao", dept: "lead_pm", coords: { x: -85, y: 0, z: -65 }, color: "#38bdf8", hex: 0x38bdf8 },
            { name: "Rik", title: "Cảnh Sát Rủi Ro (CRO)", dept: "risk_council", coords: { x: -55, y: 0, z: -35 }, color: "#ef4444", hex: 0xef4444 },
            { name: "Hash", title: "Trinh Sát Tin Tức", dept: "news_scout", coords: { x: 55, y: 0, z: -65 }, color: "#06b6d4", hex: 0x06b6d4 },
            { name: "Meme", title: "Đội Khớp Lệnh OMS", dept: "execution_oms", coords: { x: 85, y: 0, z: -35 }, color: "#10b981", hex: 0x10b981 },
            { name: "Deck", title: "Săn Chênh Lệch Giá", dept: "arbitrage_desk", coords: { x: 105, y: 0, z: -75 }, color: "#8b5cf6", hex: 0x8b5cf6 },
            { name: "Palermo", title: "Trưởng Ban Xu Hướng", dept: "quant_lab", coords: { x: -85, y: 0, z: 65 }, color: "#a855f7", hex: 0xa855f7 },
            { name: "Tory", title: "Săn Sóng Đột Phá", dept: "breakout_hunter", coords: { x: -55, y: 0, z: 95 }, color: "#f59e0b", hex: 0xf59e0b },
            { name: "Volt", title: "Đo Lường Biến Động", dept: "volatility_lab", coords: { x: -105, y: 0, z: 105 }, color: "#ec4899", hex: 0xec4899 },
            { name: "Sniper", title: "Tích Sản Spot DCA", dept: "spot_dca", coords: { x: 55, y: 0, z: 65 }, color: "#14b8a6", hex: 0x14b8a6 },
            { name: "Prof", title: "Gác Cổng Thanh Lý", dept: "cvar_stress", coords: { x: 85, y: 0, z: 95 }, color: "#f43f5e", hex: 0xf43f5e },
            { name: "Core", title: "Kế Toán & Bài Học", dept: "accounting_pm", coords: { x: 105, y: 0, z: 50 }, color: "#10b981", hex: 0x10b981 },
            { name: "Square", title: "Cộng Đồng & Square", dept: "community_affiliate", coords: { x: 105, y: 0, z: 120 }, color: "#3b82f6", hex: 0x3b82f6 }
        ];

        AGENTS.forEach(ag => {
            const podGroup = new THREE.Group();
            podGroup.position.set(ag.coords.x, ag.coords.y, ag.coords.z);
            podGroup.userData = { agentName: ag.name, title: ag.title, color: ag.color };

            // 1. Hexagonal Base Pedestal
            const baseGeo = new THREE.CylinderGeometry(10, 11, 2.5, 6);
            const baseMat = new THREE.MeshStandardMaterial({
                color: 0x111827,
                roughness: 0.3,
                metalness: 0.85
            });
            const baseMesh = new THREE.Mesh(baseGeo, baseMat);
            baseMesh.position.y = 1.25;
            baseMesh.receiveShadow = true;
            podGroup.add(baseMesh);

            // 2. Emissive Holographic Ring on Pedestal
            const ringGeo = new THREE.RingGeometry(9.6, 10.2, 6);
            const ringMat = new THREE.MeshBasicMaterial({
                color: ag.hex,
                side: THREE.DoubleSide,
                transparent: true,
                opacity: 0.95
            });
            const ringMesh = new THREE.Mesh(ringGeo, ringMat);
            ringMesh.rotation.x = -Math.PI / 2;
            ringMesh.position.y = 2.55;
            podGroup.add(ringMesh);

            // 3. Workstation Trading Desk
            const desk = this.buildWorkstationDesk(ag);
            podGroup.add(desk);

            // 4. Humanoid 3D Character Model
            const humanoid = this.buildHumanoidCharacter(ag);
            humanoid.position.set(0, 0, -1.8); // Sitting at chair
            podGroup.add(humanoid);

            // Register in Autonomous RPG Simulation
            this.humanoids[ag.name] = {
                name: ag.name,
                title: ag.title,
                hex: ag.hex,
                homePos: new THREE.Vector3(ag.coords.x, ag.coords.y, ag.coords.z),
                currentPos: new THREE.Vector3(ag.coords.x, ag.coords.y, ag.coords.z),
                targetPos: new THREE.Vector3(ag.coords.x, ag.coords.y, ag.coords.z),
                state: 'IDLE_DESK', // 'IDLE_DESK', 'WALKING', 'COFFEE_BREAK', 'WAR_ROOM_DEBATE', 'EMERGENCY_SPRINT'
                speed: 12.0,
                scheduleTimer: 8.0 + Math.random() * 15.0,
                speechTimer: 5.0 + Math.random() * 10.0,
                group: humanoid,
                podGroup: podGroup
            };

            // 5. Dedicated Agent Point Light
            const pLight = new THREE.PointLight(ag.hex, 1.8, 35);
            pLight.position.set(0, 7, 0);
            podGroup.add(pLight);

            // 6. Billboard Label (Always facing camera)
            const labelSprite = this.createBillboardText(ag.name, ag.title, ag.color);
            labelSprite.position.set(0, 15.5, 0);
            podGroup.add(labelSprite);

            // 7. Interactive Hitbox for Raycasting (transparent: true, opacity: 0 for reliable Three.js raycasting)
            const hitGeo = new THREE.CylinderGeometry(14, 14, 24, 12);
            const hitMat = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false });
            const hitMesh = new THREE.Mesh(hitGeo, hitMat);
            hitMesh.position.y = 10;
            hitMesh.userData = { isAgentHitbox: true, agentName: ag.name };
            podGroup.add(hitMesh);

            // Recursively tag all meshes in the pod (desk, screens, character) so clicking anything interacts
            podGroup.traverse(child => {
                if (child.isMesh || child.isSprite) {
                    child.userData.agentName = ag.name;
                    child.userData.isAgentHitbox = true;
                }
            });

            this.scene.add(podGroup);
            this.agentPods[ag.name] = podGroup;
        });
    }

    createPhysicalInfrastructure() {
        this.infraGroup = new THREE.Group();
        this.powerGroup = new THREE.Group();
        this.fiberGroup = new THREE.Group();
        this.telecomGroup = new THREE.Group();
        this.serverGroup = new THREE.Group();

        this.infraGroup.add(this.powerGroup);
        this.infraGroup.add(this.fiberGroup);
        this.infraGroup.add(this.telecomGroup);
        this.infraGroup.add(this.serverGroup);

        this.createPowerGrid();
        this.createFiberRouting();
        this.createServerRacks();
        this.createTelecomRelays();

        this.scene.add(this.infraGroup);
    }

    createPowerGrid() {
        // 1. Two Main High-Voltage Substation PDUs
        const pduConfigs = [
            { pos: new THREE.Vector3(-115, 0, -45), label: "⚡ PDU SUBSTATION A", sub: "Tier-4 Feed A · 230V / 50Hz", color: "#f59e0b" },
            { pos: new THREE.Vector3(115, 0, 45), label: "⚡ PDU SUBSTATION B", sub: "Turbine Gen & UPS · 100% Online", color: "#fbbf24" }
        ];

        pduConfigs.forEach(cfg => {
            const pdu = new THREE.Group();
            pdu.position.copy(cfg.pos);

            // Concrete Base Pad
            const padGeo = new THREE.BoxGeometry(18, 1.2, 14);
            const padMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.7, metalness: 0.3 });
            const pad = new THREE.Mesh(padGeo, padMat);
            pad.position.y = 0.6;
            pdu.add(pad);

            // Transformer Housing Body
            const bodyGeo = new THREE.BoxGeometry(14, 9, 10);
            const bodyMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.3, metalness: 0.85 });
            const body = new THREE.Mesh(bodyGeo, bodyMat);
            body.position.y = 5.7;
            pdu.add(body);

            // Hazard Caution Band (Yellow/Black striped effect)
            const stripeGeo = new THREE.BoxGeometry(14.2, 1.2, 10.2);
            const stripeMat = new THREE.MeshStandardMaterial({ color: 0xeab308, emissive: 0x854d0e, roughness: 0.4 });
            const stripe = new THREE.Mesh(stripeGeo, stripeMat);
            stripe.position.y = 2.2;
            pdu.add(stripe);

            // Dual Roof Exhaust Cooling Fans
            [-3.5, 3.5].forEach(xOff => {
                const fanRim = new THREE.Mesh(
                    new THREE.CylinderGeometry(2.2, 2.2, 0.6, 16),
                    new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.9 })
                );
                fanRim.position.set(xOff, 10.5, 0);
                pdu.add(fanRim);

                // Fan Blades (cross)
                const bladeGeo = new THREE.BoxGeometry(3.6, 0.1, 0.6);
                const bladeMat = new THREE.MeshBasicMaterial({ color: 0x0284c7 });
                const blade = new THREE.Mesh(bladeGeo, bladeMat);
                blade.position.set(xOff, 10.7, 0);
                pdu.add(blade);
                this.serverFans.push(blade);
            });

            // Status Beacon Point Light
            const beacon = new THREE.PointLight(0xf59e0b, 1.5, 35);
            beacon.position.set(0, 11, 0);
            pdu.add(beacon);

            // Billboard Label
            const tag = this.createBillboardText(cfg.label, cfg.sub, cfg.color);
            tag.position.set(0, 15, 0);
            pdu.add(tag);

            this.powerGroup.add(pdu);
        });

        // 2. High-Voltage Power Busway Conduits (Amber Glowing Tubes)
        // Connect Substation A and B to Core and all 10 Agent Pods
        const pduA = new THREE.Vector3(-115, 0.4, -45);
        const pduB = new THREE.Vector3(115, 0.4, 45);
        const corePos = new THREE.Vector3(0, 0.4, 0);

        const powerTargets = [
            { pos: corePos, pdu: pduA },
            { pos: corePos, pdu: pduB }
        ];

        // Route to each agent pod from the closest substation
        for (let name in this.agentPods) {
            const podPos = this.agentPods[name].position;
            const distA = podPos.distanceTo(pduA);
            const distB = podPos.distanceTo(pduB);
            powerTargets.push({
                pos: new THREE.Vector3(podPos.x, 0.4, podPos.z),
                pdu: distA < distB ? pduA : pduB
            });
        }

        const buswayMat = new THREE.MeshStandardMaterial({
            color: 0xb45309,
            emissive: 0xf59e0b,
            emissiveIntensity: 0.85,
            roughness: 0.25,
            metalness: 0.8
        });

        powerTargets.forEach((target, idx) => {
            // Midpoint waypoint with curvature
            const mid = new THREE.Vector3().addVectors(target.pdu, target.pos).multiplyScalar(0.5);
            mid.y = 0.55;
            // Slight arch for realistic industrial routing
            mid.x += (Math.sin(idx * 1.7) * 8);
            mid.z += (Math.cos(idx * 1.7) * 8);

            const curve = new THREE.CatmullRomCurve3([
                target.pdu.clone(),
                mid,
                target.pos.clone()
            ]);

            const tubeGeo = new THREE.TubeGeometry(curve, 24, 0.42, 8, false);
            const tubeMesh = new THREE.Mesh(tubeGeo, buswayMat);
            this.powerGroup.add(tubeMesh);

            // Electricity spark particles traveling along the busway
            const sparkGeo = new THREE.SphereGeometry(0.65, 8, 8);
            const sparkMat = new THREE.MeshBasicMaterial({ color: 0xfffbeb });
            const sparkMesh = new THREE.Mesh(sparkGeo, sparkMat);
            this.powerGroup.add(sparkMesh);

            this.powerSparks.push({
                mesh: sparkMesh,
                curve: curve,
                progress: Math.random(),
                speed: 0.003 + Math.random() * 0.004
            });
        });
    }

    createFiberRouting() {
        // 1. Central Low-Latency Switching Router Hub (Arista / Cisco HFT Node)
        const routerHub = new THREE.Group();
        routerHub.position.set(0, 0, 22);

        const rBaseGeo = new THREE.CylinderGeometry(4.5, 5.2, 1.8, 6);
        const rBaseMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.2, metalness: 0.9 });
        const rBase = new THREE.Mesh(rBaseGeo, rBaseMat);
        rBase.position.y = 0.9;
        routerHub.add(rBase);

        // Glowing Blue Optical Switch Core
        const rCoreGeo = new THREE.CylinderGeometry(3.6, 3.6, 2.2, 6);
        const rCoreMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4, wireframe: true });
        const rCore = new THREE.Mesh(rCoreGeo, rCoreMat);
        rCore.position.y = 2.4;
        routerHub.add(rCore);

        const routerLight = new THREE.PointLight(0x06b6d4, 2.0, 30);
        routerLight.position.set(0, 4, 0);
        routerHub.add(routerLight);

        const tag = this.createBillboardText("🌐 CORE ROUTER (HFT)", "Arista 7130 · 1.45 Gbps Dark Fiber", "#06b6d4");
        tag.position.set(0, 8, 0);
        routerHub.add(tag);

        this.fiberGroup.add(routerHub);

        // 2. Optical Fiber Tubes & High-Speed Data Photon Packets
        const fiberMat = new THREE.MeshStandardMaterial({
            color: 0x0284c7,
            emissive: 0x00f2fe,
            emissiveIntensity: 0.95,
            transparent: true,
            opacity: 0.85,
            roughness: 0.1,
            metalness: 0.9
        });

        const hubPos = new THREE.Vector3(0, 0.45, 22);

        for (let name in this.agentPods) {
            const podPos = this.agentPods[name].position;
            const target = new THREE.Vector3(podPos.x, 0.45, podPos.z);

            const mid = new THREE.Vector3().addVectors(hubPos, target).multiplyScalar(0.5);
            mid.y = 0.52;
            mid.x += (Math.sin(podPos.z * 0.1) * 6);
            mid.z += (Math.cos(podPos.x * 0.1) * 6);

            const curve = new THREE.CatmullRomCurve3([hubPos.clone(), mid, target]);
            const tubeGeo = new THREE.TubeGeometry(curve, 24, 0.32, 8, false);
            const tubeMesh = new THREE.Mesh(tubeGeo, fiberMat);
            this.fiberGroup.add(tubeMesh);

            // Multiple animated photon packets traveling along each fiber route
            for (let p = 0; p < 2; p++) {
                const isBuyPacket = p === 0;
                const pColor = isBuyPacket ? 0x38bdf8 : 0xc084fc;
                const pMesh = new THREE.Mesh(
                    new THREE.SphereGeometry(0.52, 8, 8),
                    new THREE.MeshBasicMaterial({ color: pColor })
                );
                this.fiberGroup.add(pMesh);

                this.fiberPackets.push({
                    mesh: pMesh,
                    curve: curve,
                    progress: Math.random(),
                    speed: 0.007 + Math.random() * 0.006,
                    direction: Math.random() > 0.5 ? 1 : -1
                });
            }
        }
    }

    createServerRacks() {
        // 4 Server Rack Pods in peripheral clusters
        const rackPositions = [
            { pos: new THREE.Vector3(-65, 0, 20), rot: 0.35, label: "COMPUTE CLUSTER 01" },
            { pos: new THREE.Vector3(65, 0, -20), rot: -0.35, label: "COMPUTE CLUSTER 02" },
            { pos: new THREE.Vector3(-25, 0, -75), rot: 1.2, label: "EDGE AI ENGINE 03" },
            { pos: new THREE.Vector3(25, 0, 75), rot: -1.2, label: "HIGH-WATER CACHE 04" }
        ];

        rackPositions.forEach(cfg => {
            const cluster = new THREE.Group();
            cluster.position.copy(cfg.pos);
            cluster.rotation.y = cfg.rot;

            // Base Pad
            const bPad = new THREE.Mesh(
                new THREE.BoxGeometry(15, 0.8, 8),
                new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.8 })
            );
            bPad.position.y = 0.4;
            cluster.add(bPad);

            // Pair of 42U Server Racks
            [-3.6, 3.6].forEach(xOffset => {
                const cabinet = new THREE.Group();
                cabinet.position.set(xOffset, 0, 0);

                // Cabinet Frame
                const frameGeo = new THREE.BoxGeometry(6.2, 14, 5.0);
                const frameMat = new THREE.MeshStandardMaterial({ color: 0x0b1120, roughness: 0.3, metalness: 0.85 });
                const frame = new THREE.Mesh(frameGeo, frameMat);
                frame.position.y = 7.8;
                cabinet.add(frame);

                // Translucent Dark Acrylic Glass Door
                const doorGeo = new THREE.BoxGeometry(5.8, 13.2, 0.2);
                const doorMat = new THREE.MeshStandardMaterial({
                    color: 0x0284c7,
                    roughness: 0.1,
                    metalness: 0.9,
                    transparent: true,
                    opacity: 0.45
                });
                const door = new THREE.Mesh(doorGeo, doorMat);
                door.position.set(0, 7.8, 2.55);
                cabinet.add(door);

                // 6 Stacked Server Blade Modules with LED Arrays
                for (let b = 0; b < 6; b++) {
                    const bladeY = 3.2 + b * 1.8;
                    const bladeMesh = new THREE.Mesh(
                        new THREE.BoxGeometry(5.4, 1.4, 4.4),
                        new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.7 })
                    );
                    bladeMesh.position.set(0, bladeY, 0);
                    cabinet.add(bladeMesh);

                    // 4 LED Status Dots per blade
                    for (let l = 0; l < 4; l++) {
                        const ledColor = l === 0 ? 0x10b981 : (l === 1 ? 0x38bdf8 : (l === 2 ? 0xf59e0b : 0x10b981));
                        const ledMesh = new THREE.Mesh(
                            new THREE.BoxGeometry(0.3, 0.3, 0.1),
                            new THREE.MeshBasicMaterial({ color: ledColor })
                        );
                        ledMesh.position.set(-1.8 + l * 1.2, bladeY, 2.3);
                        cabinet.add(ledMesh);
                        this.serverLeds.push({ mesh: ledMesh, origColor: ledColor });
                    }
                }

                cluster.add(cabinet);
            });

            // Overhead Label
            const tag = this.createBillboardText(`🖥️ ${cfg.label}`, "42U Blade Racks · Dual Feed Active", "#10b981");
            tag.position.set(0, 17, 0);
            cluster.add(tag);

            this.serverGroup.add(cluster);
        });
    }

    createTelecomRelays() {
        // 1. High-Bandwidth Microwave Relay Tower & Satellite Parabolic Dish (Tokyo/SG-1 Link)
        const tower = new THREE.Group();
        tower.position.set(118, 0, -65);

        // Lattice Mast Base
        const mastGeo = new THREE.CylinderGeometry(2.2, 4.2, 34, 6);
        const mastMat = new THREE.MeshStandardMaterial({ color: 0x334155, wireframe: true });
        const mast = new THREE.Mesh(mastGeo, mastMat);
        mast.position.y = 17;
        tower.add(mast);

        // Solid Central Core Column
        const coreCol = new THREE.Mesh(
            new THREE.CylinderGeometry(1.2, 1.6, 34, 12),
            new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.9 })
        );
        coreCol.position.y = 17;
        tower.add(coreCol);

        // Parabolic Microwave Dish (8m Diameter)
        const dishGeo = new THREE.SphereGeometry(6.2, 24, 16, 0, Math.PI * 2, 0, Math.PI / 2.3);
        const dishMat = new THREE.MeshStandardMaterial({
            color: 0xf8fafc,
            roughness: 0.2,
            metalness: 0.85,
            side: THREE.DoubleSide
        });
        const dish = new THREE.Mesh(dishGeo, dishMat);
        dish.position.set(0, 34, 0);
        dish.rotation.x = -Math.PI / 3.8; // Angled skyward towards satellites
        dish.rotation.y = Math.PI / 4;
        tower.add(dish);

        // Feed Horn in center of dish
        const hornGeo = new THREE.CylinderGeometry(0.3, 0.8, 4.0, 8);
        const hornMat = new THREE.MeshStandardMaterial({ color: 0x38bdf8, emissive: 0x38bdf8, emissiveIntensity: 0.8 });
        const horn = new THREE.Mesh(hornGeo, hornMat);
        horn.position.set(0, 36.5, 1.8);
        horn.rotation.x = -Math.PI / 3.8;
        tower.add(horn);

        // Pulsating Microwave Laser Link Beam to the sky
        const beamGeo = new THREE.CylinderGeometry(0.2, 0.45, 180, 8);
        const beamMat = new THREE.MeshBasicMaterial({
            color: 0x38bdf8,
            transparent: true,
            opacity: 0.65,
            blending: THREE.AdditiveBlending
        });
        const beam = new THREE.Mesh(beamGeo, beamMat);
        beam.position.set(0, 124, 38);
        beam.rotation.x = -Math.PI / 3.8;
        tower.add(beam);
        this.microwaveBeam = beam;

        // Tower Beacon Light
        const towerBeacon = new THREE.PointLight(0x38bdf8, 2.5, 60);
        towerBeacon.position.set(0, 36, 0);
        tower.add(towerBeacon);

        const tag = this.createBillboardText("📡 MICROWAVE RELAY TOWER", "Direct Line to Binance Tokyo/SG-1 · 18ms", "#38bdf8");
        tag.position.set(0, 42, 0);
        tower.add(tag);

        this.telecomGroup.add(tower);

        // 2. Wi-Fi 7 Enterprise Access Points (AP Poles with expanding wireless waves)
        const apLocations = [
            new THREE.Vector3(-50, 0, -55),
            new THREE.Vector3(50, 0, 55),
            new THREE.Vector3(0, 0, -85)
        ];

        apLocations.forEach(pos => {
            const ap = new THREE.Group();
            ap.position.copy(pos);

            // Pole
            const poleGeo = new THREE.CylinderGeometry(0.35, 0.45, 11, 8);
            const poleMat = new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.9 });
            const pole = new THREE.Mesh(poleGeo, poleMat);
            pole.position.y = 5.5;
            ap.add(pole);

            // Saucer AP Dome
            const domeGeo = new THREE.CylinderGeometry(1.8, 2.2, 0.6, 16);
            const domeMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.2 });
            const dome = new THREE.Mesh(domeGeo, domeMat);
            dome.position.y = 11.2;
            ap.add(dome);

            // Glowing Indicator Ring on AP Dome
            const indGeo = new THREE.RingGeometry(1.2, 1.5, 16);
            const indMat = new THREE.MeshBasicMaterial({ color: 0x10b981, side: THREE.DoubleSide });
            const indRing = new THREE.Mesh(indGeo, indMat);
            indRing.rotation.x = -Math.PI / 2;
            indRing.position.y = 11.55;
            ap.add(indRing);

            // 3 Expanding Concentric Radio Wave Ripples per AP
            for (let w = 0; w < 3; w++) {
                const rippleGeo = new THREE.RingGeometry(1.5, 2.0, 32);
                const rippleMat = new THREE.MeshBasicMaterial({
                    color: 0x38bdf8,
                    transparent: true,
                    opacity: 0.7,
                    side: THREE.DoubleSide,
                    blending: THREE.AdditiveBlending
                });
                const ripple = new THREE.Mesh(rippleGeo, rippleMat);
                ripple.rotation.x = -Math.PI / 2;
                ripple.position.y = 11.6;
                ap.add(ripple);

                this.wifiRipples.push({
                    mesh: ripple,
                    phase: w * 0.33,
                    speed: 0.008
                });
            }

            this.telecomGroup.add(ap);
        });
    }

    toggleLayer(name, forceState = null) {
        if (this.layerVisibility[name] === undefined) return false;
        const newState = forceState !== null ? forceState : !this.layerVisibility[name];
        this.layerVisibility[name] = newState;

        if (name === 'power' && this.powerGroup) this.powerGroup.visible = newState;
        if (name === 'fiber' && this.fiberGroup) this.fiberGroup.visible = newState;
        if (name === 'server' && this.serverGroup) this.serverGroup.visible = newState;
        if (name === 'telecom' && this.telecomGroup) this.telecomGroup.visible = newState;

        console.log(`[3D World] Layer ${name} toggled: ${newState}`);
        return newState;
    }

    createBillboardText(title, subtitle, accentColor = "#38bdf8") {
        const canvas = document.createElement('canvas');
        canvas.width = 512;
        canvas.height = 160;
        const ctx = canvas.getContext('2d');

        // Background Glass Plate
        ctx.fillStyle = 'rgba(10, 16, 31, 0.85)';
        ctx.strokeStyle = accentColor;
        ctx.lineWidth = 4;
        this.roundRect(ctx, 10, 10, 492, 140, 16);
        ctx.fill();
        ctx.stroke();

        // Accent indicator badge
        ctx.fillStyle = accentColor;
        ctx.beginPath();
        ctx.arc(45, 52, 14, 0, Math.PI * 2);
        ctx.fill();

        // Title
        ctx.font = 'bold 36px "Segoe UI", Roboto, sans-serif';
        ctx.fillStyle = '#ffffff';
        ctx.fillText(title, 75, 62);

        // Subtitle / Department Duty
        ctx.font = '500 24px "Segoe UI", Roboto, sans-serif';
        ctx.fillStyle = accentColor;
        ctx.fillText(subtitle, 75, 110);

        const texture = new THREE.CanvasTexture(canvas);
        const spriteMat = new THREE.SpriteMaterial({
            map: texture,
            transparent: true,
            depthTest: false
        });
        const sprite = new THREE.Sprite(spriteMat);
        sprite.scale.set(15, 4.8, 1.0);
        return sprite;
    }

    show3DSpeechBubble(agentName, speechText) {
        const pod = this.agentPods[agentName];
        if (!pod) return;

        // Remove old bubble if exists
        if (this.speechBubbles[agentName]) {
            pod.remove(this.speechBubbles[agentName]);
            delete this.speechBubbles[agentName];
        }

        const canvas = document.createElement('canvas');
        canvas.width = 640;
        canvas.height = 200;
        const ctx = canvas.getContext('2d');

        // Glass bubble styling
        ctx.fillStyle = 'rgba(15, 23, 42, 0.95)';
        ctx.strokeStyle = pod.userData.color || '#38bdf8';
        ctx.lineWidth = 6;
        this.roundRect(ctx, 12, 12, 616, 176, 20);
        ctx.fill();
        ctx.stroke();

        // Speech Text wrapped
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 24px "Segoe UI", sans-serif';
        this.wrapText(ctx, speechText, 35, 55, 570, 32);

        const texture = new THREE.CanvasTexture(canvas);
        const spriteMat = new THREE.SpriteMaterial({ map: texture, depthTest: false });
        const sprite = new THREE.Sprite(spriteMat);
        sprite.scale.set(22, 7.0, 1.0);
        sprite.position.set(0, 22, 0);

        pod.add(sprite);
        this.speechBubbles[agentName] = sprite;

        // Auto remove bubble after 7 seconds
        setTimeout(() => {
            if (this.speechBubbles[agentName] === sprite) {
                pod.remove(sprite);
                delete this.speechBubbles[agentName];
            }
        }, 7000);
    }

    roundRect(ctx, x, y, w, h, r) {
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.lineTo(x + w - r, y);
        ctx.quadraticCurveTo(x + w, y, x + w, y + r);
        ctx.lineTo(x + w, y + h - r);
        ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
        ctx.lineTo(x + r, y + h);
        ctx.quadraticCurveTo(x, y + h, x, y + h - r);
        ctx.lineTo(x, y + r);
        ctx.quadraticCurveTo(x, y, x + r, y);
        ctx.closePath();
    }

    wrapText(ctx, text, x, y, maxWidth, lineHeight) {
        const words = text.split(' ');
        let line = '';
        let lineCount = 0;
        for (let n = 0; n < words.length; n++) {
            const testLine = line + words[n] + ' ';
            const metrics = ctx.measureText(testLine);
            if (metrics.width > maxWidth && n > 0) {
                ctx.fillText(line, x, y);
                line = words[n] + ' ';
                y += lineHeight;
                lineCount++;
                if (lineCount >= 3) {
                    ctx.fillText(line + '...', x, y);
                    return;
                }
            } else {
                line = testLine;
            }
        }
        ctx.fillText(line, x, y);
    }

    setCameraMode(mode, targetAgent = null) {
        this.cameraMode = mode;
        if (mode === 'FLYOVER') {
            if (this.controls) this.controls.autoRotate = true;
            if (this.controls) this.controls.autoRotateSpeed = 1.0;
        } else if (mode === 'ORBIT') {
            if (this.controls) this.controls.autoRotate = false;
        } else if (mode === 'FOCUS' && targetAgent && this.agentPods[targetAgent]) {
            const pod = this.agentPods[targetAgent];
            const p = pod.position;
            this.targetCameraPos = new THREE.Vector3(p.x + 25, p.y + 20, p.z + 25);
            this.targetLookAt = new THREE.Vector3(p.x, p.y + 8, p.z);
        }
    }

    setPreset(presetName) {
        const p = this.presets[presetName];
        if (!p) return;
        this.currentPreset = presetName;

        if (this.skyMat) {
            this.skyMat.uniforms.topColor.value.setHex(p.skyTop);
            this.skyMat.uniforms.bottomColor.value.setHex(p.skyHorizon);
        }
        if (this.sunLight) this.sunLight.color.setHex(p.sunColor);
        if (this.ambientLight) this.ambientLight.color.setHex(p.ambient);
        if (this.scene.fog) this.scene.fog.color.setHex(p.skyTop);
    }

    onPointerMove(event) {
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.scene.children, true);
        
        let foundPod = null;
        for (let hit of intersects) {
            let cur = hit.object;
            while (cur && cur !== this.scene) {
                if (cur.userData && (cur.userData.agentName || cur.userData.isAgentHitbox)) {
                    foundPod = cur.userData.agentName;
                    break;
                }
                cur = cur.parent;
            }
            if (foundPod) break;
        }

        if (foundPod !== this.hoveredPod) {
            this.hoveredPod = foundPod;
            this.renderer.domElement.style.cursor = foundPod ? 'pointer' : 'default';
        }
    }

    onPointerClick(event) {
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.scene.children, true);
        
        let clickedPod = null;
        for (let hit of intersects) {
            let cur = hit.object;
            while (cur && cur !== this.scene) {
                if (cur.userData && cur.userData.agentName) {
                    clickedPod = cur.userData.agentName;
                    break;
                }
                cur = cur.parent;
            }
            if (clickedPod) break;
        }

        if (clickedPod) {
            this.triggerAgentInteraction(clickedPod);
        } else if (this.hoveredPod) {
            this.triggerAgentInteraction(this.hoveredPod);
        }
    }

    onTouchStart(event) {
        if (event.touches.length === 1) {
            const touch = event.touches[0];
            const rect = this.renderer.domElement.getBoundingClientRect();
            this.mouse.x = ((touch.clientX - rect.left) / rect.width) * 2 - 1;
            this.mouse.y = -((touch.clientY - rect.top) / rect.height) * 2 + 1;

            this.raycaster.setFromCamera(this.mouse, this.camera);
            const intersects = this.raycaster.intersectObjects(this.scene.children, true);
            for (let hit of intersects) {
                let cur = hit.object;
                while (cur && cur !== this.scene) {
                    if (cur.userData && cur.userData.agentName) {
                        this.triggerAgentInteraction(cur.userData.agentName);
                        return;
                    }
                    cur = cur.parent;
                }
            }
        }
    }

    triggerAgentInteraction(agentName) {
        console.log(`[3D World] Agent Clicked: ${agentName}`);
        this.setCameraMode('FOCUS', agentName);
        
        // Humanoid Wave & Speak Animation
        const npc = this.humanoids ? this.humanoids[agentName] : null;
        if (npc && npc.group && npc.group.bones) {
            const b = npc.group.bones;
            // Wave greeting
            b.rightArm.rotation.x = -2.2;
            b.rightForearm.rotation.z = 0.6;
            
            const dialogues = this.agentLessonDialogues[agentName] || ["Sẵn sàng nhận lệnh từ Boss!"];
            const text = dialogues[Math.floor(Math.random() * dialogues.length)];
            this.showSpeechBubble(agentName, `Boss đã gọi! ${text}`, 7.0);
        }

        // Dispatch custom DOM event for pixel_floor.js to catch and open modal/dialogue
        const ev = new CustomEvent('astra-agent-clicked', { detail: { agentName } });
        window.dispatchEvent(ev);
    }

    updateAutonomousRPGNPCs(delta, time) {
        if (!this.humanoids) return;

        for (let name in this.humanoids) {
            const npc = this.humanoids[name];
            if (!npc || !npc.group || !npc.group.bones) continue;

            const b = npc.group.bones;
            npc.scheduleTimer -= delta;
            npc.speechTimer -= delta;

            // 1. Periodic Dialogue Bubble from 37 Trading Lessons
            if (npc.speechTimer <= 0) {
                npc.speechTimer = 18.0 + Math.random() * 25.0;
                const dialogues = this.agentLessonDialogues[name] || ["Đang giám sát thị trường..."];
                const text = dialogues[Math.floor(Math.random() * dialogues.length)];
                this.showSpeechBubble(name, text, 6.0);
            }

            // 2. Autonomous Scheduler / State Machine
            if (npc.scheduleTimer <= 0) {
                npc.scheduleTimer = 22.0 + Math.random() * 28.0;

                if (npc.state === 'IDLE_DESK') {
                    const destinations = [
                        { state: 'COFFEE_BREAK', pos: new THREE.Vector3(this.rpgWaypoints.coffeeBar.x + (Math.random() - 0.5) * 16, 0, this.rpgWaypoints.coffeeBar.z + (Math.random() - 0.5) * 8) },
                        { state: 'WAR_ROOM_DEBATE', pos: new THREE.Vector3(this.rpgWaypoints.centerHub.x + Math.cos(Math.random() * 6.28) * 18, 0, this.rpgWaypoints.centerHub.z + Math.sin(Math.random() * 6.28) * 18) }
                    ];
                    const choice = destinations[Math.floor(Math.random() * destinations.length)];
                    npc.state = 'WALKING';
                    npc.nextState = choice.state;
                    npc.targetPos.copy(choice.pos);
                } else if (npc.state === 'COFFEE_BREAK' || npc.state === 'WAR_ROOM_DEBATE') {
                    npc.state = 'WALKING';
                    npc.nextState = 'IDLE_DESK';
                    npc.targetPos.copy(npc.homePos);
                }
            }

            // 3. State Execution & Hierarchical Bone Kinematics
            if (npc.state === 'IDLE_DESK') {
                npc.group.position.set(0, 0, -1.8);
                npc.group.rotation.set(0, 0, 0);

                // Sitting Pose
                b.pelvis.position.y = 3.6;
                b.leftLeg.rotation.x = -1.5;
                b.rightLeg.rotation.x = -1.5;
                b.leftCalf.rotation.x = 1.5;
                b.rightCalf.rotation.x = 1.5;

                // Typing at Workstation Monitors
                b.leftArm.rotation.x = -1.1;
                b.rightArm.rotation.x = -1.1;
                b.leftForearm.rotation.x = -0.5 + Math.sin(time * 12 + npc.homePos.x) * 0.12;
                b.rightForearm.rotation.x = -0.5 + Math.cos(time * 14 + npc.homePos.z) * 0.12;

                // Head Scanning Monitors
                b.headGroup.rotation.y = Math.sin(time * 1.8 + npc.homePos.x) * 0.35;
                b.headGroup.rotation.x = Math.sin(time * 2.2) * 0.08;
                b.torso.rotation.x = 0.05;

            } else if (npc.state === 'WALKING' || npc.state === 'EMERGENCY_SPRINT') {
                const isSprint = (npc.state === 'EMERGENCY_SPRINT');
                const speed = isSprint ? npc.speed * 2.2 : npc.speed;
                const walkCycleRate = isSprint ? 14.0 : 7.0;

                const dir = new THREE.Vector3().subVectors(npc.targetPos, npc.currentPos);
                const dist = dir.length();

                if (dist > 1.8) {
                    dir.normalize();
                    npc.currentPos.addScaledVector(dir, speed * delta);
                    
                    const targetAngle = Math.atan2(dir.x, dir.z);
                    npc.group.rotation.y = targetAngle;

                    npc.group.position.x = npc.currentPos.x - npc.homePos.x;
                    npc.group.position.z = npc.currentPos.z - npc.homePos.z;
                    npc.group.position.y = 0;

                    // Bipedal Walking Kinematics
                    const legAngle = Math.sin(time * walkCycleRate) * (isSprint ? 0.9 : 0.6);
                    b.leftLeg.rotation.x = legAngle;
                    b.rightLeg.rotation.x = -legAngle;

                    b.leftCalf.rotation.x = Math.max(0, -legAngle * 0.7);
                    b.rightCalf.rotation.x = Math.max(0, legAngle * 0.7);

                    b.leftArm.rotation.x = -legAngle * 0.6;
                    b.rightArm.rotation.x = legAngle * 0.6;
                    b.leftForearm.rotation.x = -0.3;
                    b.rightForearm.rotation.x = -0.3;

                    b.pelvis.position.y = 5.2 + Math.abs(Math.sin(time * walkCycleRate * 2.0)) * 0.35;
                    b.torso.rotation.x = isSprint ? 0.35 : 0.08;
                    b.headGroup.rotation.y = Math.sin(time * walkCycleRate * 0.5) * 0.15;

                } else {
                    npc.state = npc.nextState || 'IDLE_DESK';
                    if (npc.state === 'COFFEE_BREAK') {
                        this.showSpeechBubble(name, "☕ Nghỉ giải lao một chút, nạp caffeine chuẩn bị săn sóng!", 5.0);
                    } else if (npc.state === 'WAR_ROOM_DEBATE') {
                        this.showSpeechBubble(name, "Hội đồng 10 Tác Tử tập trung tại War Room!", 5.0);
                    }
                }

            } else if (npc.state === 'COFFEE_BREAK') {
                b.pelvis.position.y = 5.2;
                b.leftLeg.rotation.x = 0;
                b.rightLeg.rotation.x = 0;
                b.leftCalf.rotation.x = 0;
                b.rightCalf.rotation.x = 0;

                // Holding coffee cup
                b.rightArm.rotation.x = -1.4;
                b.rightForearm.rotation.x = -0.8 + Math.sin(time * 2.0) * 0.15;
                b.leftArm.rotation.x = -0.3;
                b.leftForearm.rotation.x = -0.2;

                b.headGroup.rotation.x = -0.15 + Math.sin(time * 2.0) * 0.1;
                b.headGroup.rotation.y = Math.sin(time * 1.0) * 0.25;

            } else if (npc.state === 'WAR_ROOM_DEBATE') {
                b.pelvis.position.y = 5.2;
                b.leftLeg.rotation.x = 0.1;
                b.rightLeg.rotation.x = -0.1;
                b.leftCalf.rotation.x = 0;
                b.rightCalf.rotation.x = 0;

                // Debate Gestures
                b.leftArm.rotation.x = -0.8 + Math.sin(time * 4.0 + npc.homePos.x) * 0.3;
                b.rightArm.rotation.x = -0.8 + Math.cos(time * 3.5 + npc.homePos.z) * 0.3;
                b.leftForearm.rotation.x = -0.6;
                b.rightForearm.rotation.x = -0.6;

                b.headGroup.rotation.y = Math.sin(time * 2.5) * 0.4;
            }
        }
    }

    onWindowResize() {
        if (!this.container || !this.camera || !this.renderer) return;
        const width = this.container.clientWidth || window.innerWidth;
        const height = this.container.clientHeight || 550;
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        const delta = this.clock.getDelta();
        const time = this.clock.getElapsedTime();

        // 1. Quantum Core Animations
        if (this.coreMesh) {
            this.coreMesh.rotation.y += 0.012;
            this.coreMesh.rotation.x += 0.007;
            this.coreMesh.position.y = Math.sin(time * 2.0) * 1.5;
        }
        if (this.wireMesh) {
            this.wireMesh.rotation.y -= 0.008;
        }
        if (this.torus1) this.torus1.rotation.z += 0.02;
        if (this.torus2) this.torus2.rotation.y += 0.015;

        // 2. Autonomous RPG NPC Gameplay Life Simulation (GPT-5 / GTA-V Style)
        this.updateAutonomousRPGNPCs(delta, time);

        // War Room Hologram Candle Ring Rotation
        if (this.warRoomCandles) {
            this.warRoomCandles.rotation.y += 0.008;
        }

        // 2b. Physical Infrastructure Animations
        // A. Power Grid Electricity Sparks
        if (this.layerVisibility.power && this.powerSparks.length > 0) {
            this.powerSparks.forEach(spark => {
                spark.progress = (spark.progress + spark.speed * (delta / 0.016)) % 1.0;
                spark.curve.getPointAt(spark.progress, spark.mesh.position);
            });
        }

        // B. Dark Fiber Data Photon Packets
        if (this.layerVisibility.fiber && this.fiberPackets.length > 0) {
            this.fiberPackets.forEach(pkt => {
                pkt.progress = (pkt.progress + pkt.speed * pkt.direction * (delta / 0.016));
                if (pkt.progress > 1.0) pkt.progress -= 1.0;
                if (pkt.progress < 0.0) pkt.progress += 1.0;
                pkt.curve.getPointAt(pkt.progress, pkt.mesh.position);
            });
        }

        // C. Wi-Fi 7 Expanding Radio Waves
        if (this.layerVisibility.telecom && this.wifiRipples.length > 0) {
            this.wifiRipples.forEach(rip => {
                rip.phase = (rip.phase + rip.speed * (delta / 0.016)) % 1.0;
                rip.mesh.scale.setScalar(1.0 + rip.phase * 15.0);
                rip.mesh.material.opacity = Math.max(0, 0.7 * (1.0 - rip.phase));
            });
        }

        // D. Substation & Server Cooling Fans
        if (this.serverFans.length > 0) {
            this.serverFans.forEach(fan => {
                fan.rotation.z += 0.16;
            });
        }

        // E. Microwave Relay Laser Beam Pulse
        if (this.microwaveBeam && this.layerVisibility.telecom) {
            this.microwaveBeam.material.opacity = 0.45 + Math.sin(time * 5.0) * 0.25;
        }

        // F. Server Blade Status LEDs Flicker
        if (this.layerVisibility.server && Math.random() < 0.25 && this.serverLeds.length > 0) {
            const randIdx = Math.floor(Math.random() * this.serverLeds.length);
            const led = this.serverLeds[randIdx];
            if (led && led.mesh) {
                led.mesh.visible = !led.mesh.visible;
            }
        }

        // 3. Vector Field Update (Tellux Wind3D inspired)
        if (this.vectorField) {
            if (window.currentTelemetry) {
                this.vectorField.applyMarketTelemetry(window.currentTelemetry);
            }
            this.vectorField.update(delta);
        }

        // 4. Smooth Camera Focus Glide
        if (this.cameraMode === 'FOCUS' && this.targetCameraPos && this.targetLookAt) {
            this.camera.position.lerp(this.targetCameraPos, 0.06);
            if (this.controls) {
                this.controls.target.lerp(this.targetLookAt, 0.06);
            }
            if (this.camera.position.distanceTo(this.targetCameraPos) < 1.0) {
                this.cameraMode = 'ORBIT';
                this.targetCameraPos = null;
            }
        }

        // 5. Update OrbitControls
        if (this.controls) {
            this.controls.update();
        }

        // 6. Render
        this.renderer.render(this.scene, this.camera);

        // 7. Calculate FPS for Cockpit HUD
        this.frameCount++;
        const now = performance.now();
        if (now - this.lastFpsUpdate >= 500) {
            this.fps = Math.round((this.frameCount * 1000) / (now - this.lastFpsUpdate));
            this.frameCount = 0;
            this.lastFpsUpdate = now;
            const frametimeMs = (1000 / Math.max(this.fps, 1)).toFixed(1);
            
            const fpsEl = document.getElementById('hud-fps-val');
            if (fpsEl) fpsEl.textContent = `${this.fps} FPS`;
            const msEl = document.getElementById('hud-frametime-val');
            if (msEl) msEl.textContent = `${frametimeMs}ms`;

            const gisFps = document.getElementById('gis-fps-val');
            if (gisFps) gisFps.textContent = `${this.fps} FPS (${frametimeMs}ms)`;
        }
    }

    setVectorMode(mode) {
        if (this.vectorField) {
            this.vectorField.setMode(mode);
        }
    }

    resetCamera() {
        this.cameraMode = 'ORBIT';
        if (this.controls) {
            this.controls.autoRotate = false;
            this.controls.target.set(0, 8, 0);
        }
        this.camera.position.set(0, 110, 175);
    }
}

window.Astra3DWorldEngine = Astra3DWorldEngine;
