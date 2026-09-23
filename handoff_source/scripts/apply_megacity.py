import sys
import os

target_path = r"c:\sunMy\trading_bot\web\static\js\pixel_floor.js"

with open(target_path, "r", encoding="utf-8") as f:
    text = f.read()

# 1. Sound: Add 'turbo' to playRetroSound
old_sound_target = """        } else if (type === 'gold') {
            // Big victory fanfare
            osc.type = 'square';
            osc.frequency.setValueAtTime(440, now); // A4
            osc.frequency.setValueAtTime(554.37, now + 0.09); // C#5
            osc.frequency.setValueAtTime(659.25, now + 0.18); // E5
            osc.frequency.setValueAtTime(880, now + 0.27); // A5
            gain.gain.setValueAtTime(0.18, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
            osc.start(now);
            osc.stop(now + 0.6);
        }"""

new_sound_replacement = """        } else if (type === 'gold') {
            // Big victory fanfare
            osc.type = 'square';
            osc.frequency.setValueAtTime(440, now); // A4
            osc.frequency.setValueAtTime(554.37, now + 0.09); // C#5
            osc.frequency.setValueAtTime(659.25, now + 0.18); // E5
            osc.frequency.setValueAtTime(880, now + 0.27); // A5
            gain.gain.setValueAtTime(0.18, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);
            osc.start(now);
            osc.stop(now + 0.6);
        } else if (type === 'turbo') {
            // High-octane Ferrari/Lambo engine rev & turbo flutter sound
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(120, now);
            osc.frequency.exponentialRampToValueAtTime(480, now + 0.28);
            osc.frequency.exponentialRampToValueAtTime(210, now + 0.55);
            gain.gain.setValueAtTime(0.25, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.62);
            osc.start(now);
            osc.stop(now + 0.62);
        }"""

if old_sound_target in text:
    text = text.replace(old_sound_target, new_sound_replacement, 1)
    print("1. Added 'turbo' sound successfully.")
else:
    print("WARNING: Could not find old_sound_target")

# 2. Constructor: Add state properties
old_ctor_target = """        // Autonomous CEO Patrol & 3-Way Dialogue State
        this.isAutonomousPatrol = false;"""

new_ctor_replacement = """        // Megacity Skyline, Supercars & FPV Cyber Companion State
        this.fpvCompanionGroup = null;
        this.fpvCompanionEyeVisor = null;
        this.fpvLeftWing = null;
        this.fpvRightWing = null;
        this.fpvLeftTail = null;
        this.fpvRightTail = null;
        this.fpvHalo = null;
        this.skylineBeacons = [];
        this.skyCruisers = [];
        this.supercars = [];
        this.nearbySupercar = null;
        this.deskAstraAvatar = null;

        // Autonomous CEO Patrol & 3-Way Dialogue State
        this.isAutonomousPatrol = false;"""

if old_ctor_target in text:
    text = text.replace(old_ctor_target, new_ctor_replacement, 1)
    print("2. Added constructor state successfully.")
else:
    print("WARNING: Could not find old_ctor_target")

# 3. Init: Add build calls
old_init_target = """        this.buildDataConduitsAndPackets();
        this.buildAvatars();
        this.setupEvents();"""

new_init_replacement = """        this.buildDataConduitsAndPackets();
        this.buildAvatars();
        this.buildMegacitySkylineAndSupercars();
        this.buildExecutiveAssistantAstra();
        this.buildFpvCompanionAstra();
        this.setupEvents();"""

if old_init_target in text:
    text = text.replace(old_init_target, new_init_replacement, 1)
    print("3. Added init build calls successfully.")
else:
    print("WARNING: Could not find old_init_target")

# 4. getFloorHeight: Add Balcony Terrace height
old_floor_target = """        // 4. Connecting Sky-Walkways (Corridors connecting Core (0,0) to 4 Wings)"""

new_floor_replacement = """        // 4B. South VIP Balcony Terrace & Skybridge (Supercar Showroom Balcony at z = 115..175)
        if (Math.abs(x) <= 38 && z >= 115 && z <= 175) {
            return 3.0;
        }

        // 4. Connecting Sky-Walkways (Corridors connecting Core (0,0) to 4 Wings)"""

if old_floor_target in text:
    text = text.replace(old_floor_target, new_floor_replacement, 1)
    print("4. Added Balcony Terrace floor height successfully.")
else:
    print("WARNING: Could not find old_floor_target")

# 5. Insert new 3D builder methods after buildAvatars
old_avatars_target = """        this.astraBubbleSprite = this.createSpeechBubbleSprite('🤖 Astra: 12 phòng ban sẵn sàng!', 0xc084fc);
        this.astraBubbleSprite.visible = false;
        this.astraBubbleSprite.scale.set(24, 6.5, 1);
        this.scene.add(this.astraBubbleSprite);
    }"""

new_avatars_methods = """        this.astraBubbleSprite = this.createSpeechBubbleSprite('🤖 Astra: 12 phòng ban sẵn sàng!', 0xc084fc);
        this.astraBubbleSprite.visible = false;
        this.astraBubbleSprite.scale.set(24, 6.5, 1);
        this.scene.add(this.astraBubbleSprite);
    }

    /* --------------------------------------------------------------------------
       10E. BUILD MEGACITY SKYLINE & SUPERCAR SHOWROOM BALCONY (INSPIRED BY NARGOR/CAR-ACTION)
       -------------------------------------------------------------------------- */
    buildMegacitySkylineAndSupercars() {
        const megacityGroup = new THREE.Group();

        // 1. 52 Cyberpunk Illuminated Skyscrapers around the Horizon (r = 280 .. 520)
        const buildingColors = [0x0f172a, 0x0a0f1d, 0x111827, 0x050b14, 0x1e1b4b];
        const neonGlowColors = [0x00f0ff, 0x38bdf8, 0xf59e0b, 0xec4899, 0xa855f7, 0x10b981];

        const numTowers = 52;
        for (let i = 0; i < numTowers; i++) {
            const angle = (i / numTowers) * Math.PI * 2 + (Math.sin(i * 3.7) * 0.08);
            const radius = 290 + (i % 7) * 32 + (Math.sin(i * 1.5) * 25);
            const width = 22 + (i % 5) * 6;
            const depth = 22 + ((i + 2) % 5) * 6;
            const height = 110 + (i % 9) * 26 + ((i * 17) % 80);

            const towerGroup = new THREE.Group();
            towerGroup.position.set(
                Math.sin(angle) * radius,
                height / 2 - 15,
                Math.cos(angle) * radius
            );

            // Tower main body
            const bGeo = new THREE.BoxGeometry(width, height, depth);
            const bMat = new THREE.MeshStandardMaterial({
                color: buildingColors[i % buildingColors.length],
                metalness: 0.85,
                roughness: 0.25
            });
            const tower = new THREE.Mesh(bGeo, bMat);
            towerGroup.add(tower);

            // Illuminated window facade strips
            const winColor = neonGlowColors[i % neonGlowColors.length];
            const numStrips = 3 + (i % 4);
            for (let s = 0; s < numStrips; s++) {
                const stripY = -height * 0.4 + (s / numStrips) * height * 0.85;
                const winH = 4 + (s % 3) * 3;
                const winGeo = new THREE.BoxGeometry(width + 0.4, winH, depth + 0.4);
                const winMat = new THREE.MeshBasicMaterial({
                    color: winColor,
                    transparent: true,
                    opacity: 0.55 + (s % 2) * 0.25
                });
                const winStrip = new THREE.Mesh(winGeo, winMat);
                winStrip.position.y = stripY;
                towerGroup.add(winStrip);
            }

            // Rooftop Communication Antenna & Spire
            const spireH = 18 + (i % 6) * 7;
            const spireGeo = new THREE.CylinderGeometry(0.3, 1.2, spireH, 6);
            const spireMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.9 });
            const spire = new THREE.Mesh(spireGeo, spireMat);
            spire.position.y = height / 2 + spireH / 2;
            towerGroup.add(spire);

            // Flashing Red Aviation Beacon on Rooftop Spire
            const beaconGeo = new THREE.SphereGeometry(0.8, 8, 8);
            const beaconMat = new THREE.MeshBasicMaterial({ color: (i % 2 === 0 ? 0xef4444 : 0xf59e0b) });
            const beacon = new THREE.Mesh(beaconGeo, beaconMat);
            beacon.position.y = height / 2 + spireH;
            towerGroup.add(beacon);
            this.skylineBeacons.push({ mesh: beacon, phase: i * 0.35 });

            // Rooftop Billboard on select major skyscrapers
            if (i % 8 === 0) {
                const ads = [
                    'BINANCE HFT LIVE',
                    'ASTRA QUANT V3.0',
                    'WALL STREET ALGO',
                    'DEEP ALPHA LAB',
                    'CVAR SHIELD 0.0%',
                    'BYBIT PERP CLUSTER'
                ];
                const adText = ads[(i / 8) % ads.length];
                const billboard = this.createHoloSprite(adText, winColor);
                billboard.position.set(0, height / 2 + 10, 0);
                billboard.scale.set(45, 12, 1);
                towerGroup.add(billboard);
            }

            megacityGroup.add(towerGroup);
        }

        // 2. Autonomous Sky-Cruisers (Flying hover-cars in air traffic corridors)
        for (let c = 0; c < 5; c++) {
            const cruiser = new THREE.Group();
            const cBody = new THREE.Mesh(
                new THREE.BoxGeometry(7.0, 1.6, 3.2),
                new THREE.MeshStandardMaterial({ color: 0x0f172a, metalness: 0.9, roughness: 0.1 })
            );
            cruiser.add(cBody);

            const hLight = new THREE.Mesh(
                new THREE.BoxGeometry(0.4, 0.5, 2.6),
                new THREE.MeshBasicMaterial({ color: 0x00f0ff })
            );
            hLight.position.set(3.6, 0, 0);
            cruiser.add(hLight);

            const thruster = new THREE.Mesh(
                new THREE.BoxGeometry(0.4, 0.6, 2.4),
                new THREE.MeshBasicMaterial({ color: 0xec4899 })
            );
            thruster.position.set(-3.6, 0, 0);
            cruiser.add(thruster);

            cruiser.userData = {
                radius: 260 + c * 35,
                speed: 0.18 + c * 0.06,
                angle: (c * Math.PI * 2) / 5,
                baseY: 95 + c * 18
            };
            megacityGroup.add(cruiser);
            this.skyCruisers.push(cruiser);
        }

        // 3. SOUTH VIP SUPERCAR SHOWROOM TERRACE & BALCONY (Inspired by Nargor/car-action)
        const balcony = new THREE.Group();
        balcony.position.set(0, 0, 150);

        // Balcony Platform
        const balGeo = new THREE.BoxGeometry(72, 3.0, 48);
        const balMat = new THREE.MeshStandardMaterial({ color: 0x0a1020, metalness: 0.85, roughness: 0.2 });
        const balMesh = new THREE.Mesh(balGeo, balMat);
        balMesh.position.y = 1.5;
        balMesh.receiveShadow = true;
        balcony.add(balMesh);

        // Glowing Balcony Rim Edge
        const balEdge = new THREE.LineSegments(
            new THREE.EdgesGeometry(new THREE.BoxGeometry(72.4, 3.2, 48.4)),
            new THREE.LineBasicMaterial({ color: 0x00f0ff })
        );
        balEdge.position.y = 1.5;
        balcony.add(balEdge);

        // Glass Safety Railings
        const railMat = new THREE.MeshStandardMaterial({
            color: 0x38bdf8,
            transparent: true,
            opacity: 0.35,
            metalness: 0.5
        });
        const backRail = new THREE.Mesh(new THREE.BoxGeometry(72, 4.5, 0.3), railMat);
        backRail.position.set(0, 4.5, 24);
        balcony.add(backRail);

        const leftRail = new THREE.Mesh(new THREE.BoxGeometry(0.3, 4.5, 48), railMat);
        leftRail.position.set(-36, 4.5, 0);
        balcony.add(leftRail);

        const rightRail = new THREE.Mesh(new THREE.BoxGeometry(0.3, 4.5, 48), railMat);
        rightRail.position.set(36, 4.5, 0);
        balcony.add(rightRail);

        // Balcony Entrance Billboard
        const terraceBanner = this.createHoloSprite('🏎️ VIP SUPERCAR BALCONY · ĐỘI XE ĐUA QUANTUM', 0xf59e0b);
        terraceBanner.position.set(0, 14, 23.5);
        terraceBanner.scale.set(36, 5.5, 1);
        balcony.add(terraceBanner);

        // Connecting Skywalk from Central Core to Balcony
        const bridgeGeo = new THREE.BoxGeometry(16, 2.2, 55);
        const bridge = new THREE.Mesh(bridgeGeo, balMat);
        bridge.position.set(0, 1.1, -40);
        balcony.add(bridge);

        const bridgeTrim = new THREE.LineSegments(
            new THREE.EdgesGeometry(new THREE.BoxGeometry(16.3, 2.3, 55.2)),
            new THREE.LineBasicMaterial({ color: 0x38bdf8 })
        );
        bridgeTrim.position.set(0, 1.1, -40);
        balcony.add(bridgeTrim);

        // 4. SUPERCAR 1: Ferrari 488 Cyber Red GTB (Referenced from Nargor/car-action 50 Ferrari setup)
        const ferrari = this.createSupercarMesh(
            'ferrari',
            0xd90429, // Cyber Ferrari Racing Red
            0x111827, // Carbon Black
            '🏎️ FERRARI 488 GTB · RACER #01',
            'V8 TWIN-TURBO 720HP | TIKTOK NITRO READY'
        );
        ferrari.position.set(-18, 3.0, 4);
        ferrari.rotation.y = Math.PI * 0.12;
        balcony.add(ferrari);
        this.supercars.push({
            group: ferrari,
            id: 'ferrari_488',
            name: 'Ferrari 488 Cyber GTB',
            worldPos: new THREE.Vector3(-18, 3.0, 154)
        });

        // 5. SUPERCAR 2: Lamborghini Aventador SVJ Cyber Cyan
        const lambo = this.createSupercarMesh(
            'lambo',
            0x00f0ff, // Electric Cyber Cyan
            0x0f172a, // Obsidian Black
            '⚡ LAMBORGHINI SVJ · RACER #07',
            'V12 770HP | QUANTUM OVERCLOCK 350 KM/H'
        );
        lambo.position.set(18, 3.0, 4);
        lambo.rotation.y = -Math.PI * 0.12;
        balcony.add(lambo);
        this.supercars.push({
            group: lambo,
            id: 'lambo_svj',
            name: 'Lamborghini Aventador SVJ',
            worldPos: new THREE.Vector3(18, 3.0, 154)
        });

        megacityGroup.add(balcony);
        this.scene.add(megacityGroup);
        this.megacityGroup = megacityGroup;
    }

    /* --------------------------------------------------------------------------
       10E-2. CREATE PROCEDURAL SUPERCAR MESH (FERRARI & LAMBORGHINI)
       -------------------------------------------------------------------------- */
    createSupercarMesh(brand, bodyColorHex, accentColorHex, nameLabel, subLabel) {
        const car = new THREE.Group();

        const carPaintMat = new THREE.MeshStandardMaterial({
            color: bodyColorHex,
            metalness: 0.9,
            roughness: 0.15
        });
        const carbonMat = new THREE.MeshStandardMaterial({
            color: accentColorHex,
            roughness: 0.4,
            metalness: 0.8
        });
        const glassMat = new THREE.MeshStandardMaterial({
            color: 0x050c18,
            metalness: 0.95,
            roughness: 0.05,
            transparent: true,
            opacity: 0.85
        });
        const chromeWheelMat = new THREE.MeshStandardMaterial({
            color: 0xe2e8f0,
            metalness: 0.95,
            roughness: 0.1
        });
        const tireMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.8 });
        const brakeCaliperMat = new THREE.MeshBasicMaterial({ color: 0xff0055 });

        // 1. Lower Chassis & Aerodynamic Floor
        const chassis = new THREE.Mesh(new THREE.BoxGeometry(5.6, 0.45, 11.2), carbonMat);
        chassis.position.y = 0.5;
        chassis.castShadow = true;
        car.add(chassis);

        // Front Splitter
        const splitter = new THREE.Mesh(new THREE.BoxGeometry(5.8, 0.12, 1.4), carbonMat);
        splitter.position.set(0, 0.35, 5.8);
        car.add(splitter);

        // 2. Main Aerodynamic Sleek Body Shell
        const bodyGeo = new THREE.BoxGeometry(5.4, 1.1, 10.4);
        const body = new THREE.Mesh(bodyGeo, carPaintMat);
        body.position.y = 1.15;
        body.castShadow = true;
        car.add(body);

        // Sculpted Slanted Front Hood / Nose
        const hoodGeo = new THREE.ConeGeometry(3.6, 3.8, 4);
        const hood = new THREE.Mesh(hoodGeo, carPaintMat);
        hood.rotation.x = Math.PI / 2;
        hood.rotation.y = Math.PI / 4;
        hood.scale.set(1.0, 0.35, 1.0);
        hood.position.set(0, 1.15, 3.8);
        car.add(hood);

        // 3. Cabin Cockpit Canopy with Tinted Panoramic Windshield
        const cabinGeo = new THREE.BoxGeometry(4.2, 1.15, 5.0);
        const cabin = new THREE.Mesh(cabinGeo, glassMat);
        cabin.position.set(0, 2.05, -0.6);
        car.add(cabin);

        // Aerodynamic Roof Carbon Cap
        const roof = new THREE.Mesh(new THREE.BoxGeometry(3.8, 0.15, 4.4), carbonMat);
        roof.position.set(0, 2.68, -0.6);
        car.add(roof);

        // 4. Rear Carbon Fiber GT Racing Wing Spoiler
        const wingPillars = new THREE.Group();
        for (let p = -1; p <= 1; p += 2) {
            const pillar = new THREE.Mesh(new THREE.BoxGeometry(0.18, 1.2, 0.8), carbonMat);
            pillar.position.set(p * 1.8, 2.4, -4.8);
            wingPillars.add(pillar);
        }
        const gtWing = new THREE.Mesh(new THREE.BoxGeometry(5.8, 0.14, 1.4), carbonMat);
        gtWing.position.set(0, 3.0, -4.9);
        gtWing.rotation.x = -0.08;
        wingPillars.add(gtWing);
        car.add(wingPillars);

        // 5. LED Headlights & Quad Taillights
        const headLightMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff });
        for (let side = -1; side <= 1; side += 2) {
            const hl = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.25, 0.2), headLightMat);
            hl.position.set(side * 1.9, 1.25, 5.4);
            hl.rotation.y = side * 0.2;
            car.add(hl);
        }

        const tailLightMat = new THREE.MeshBasicMaterial({ color: 0xff0033 });
        for (let side = -1; side <= 1; side += 2) {
            const tl = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.25, 0.2), tailLightMat);
            tl.position.set(side * 1.8, 1.35, -5.25);
            car.add(tl);
        }

        // 6. Dual Exhaust Pipes with Glowing Blue Flame Tips
        const exhaustGroup = new THREE.Group();
        for (let side = -1; side <= 1; side += 2) {
            const pipe = new THREE.Mesh(
                new THREE.CylinderGeometry(0.24, 0.24, 0.8, 12),
                chromeWheelMat
            );
            pipe.rotation.x = Math.PI / 2;
            pipe.position.set(side * 0.9, 0.7, -5.3);
            exhaustGroup.add(pipe);

            // Blue flame interior glow
            const flame = new THREE.Mesh(
                new THREE.ConeGeometry(0.16, 0.6, 8),
                new THREE.MeshBasicMaterial({ color: 0x00f0ff })
            );
            flame.rotation.x = -Math.PI / 2;
            flame.position.set(side * 0.9, 0.7, -5.7);
            exhaustGroup.add(flame);
        }
        car.add(exhaustGroup);
        car.userData.exhaustGroup = exhaustGroup;

        // 7. 4 High-Detail Sports Wheels (Rims, Tires & Brembo Brake Calipers)
        const wheelCoords = [
            { x: -2.8, y: 0.9, z: 3.2 },
            { x: 2.8, y: 0.9, z: 3.2 },
            { x: -2.8, y: 1.0, z: -3.2 },
            { x: 2.8, y: 1.0, z: -3.2 }
        ];
        wheelCoords.forEach(pos => {
            const wGroup = new THREE.Group();
            wGroup.position.set(pos.x, pos.y, pos.z);

            const tire = new THREE.Mesh(
                new THREE.CylinderGeometry(0.9, 0.9, 0.8, 18),
                tireMat
            );
            tire.rotation.z = Math.PI / 2;
            wGroup.add(tire);

            const rim = new THREE.Mesh(
                new THREE.CylinderGeometry(0.65, 0.65, 0.82, 12),
                chromeWheelMat
            );
            rim.rotation.z = Math.PI / 2;
            wGroup.add(rim);

            const caliper = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.45, 0.35), brakeCaliperMat);
            caliper.position.set(pos.x > 0 ? -0.2 : 0.2, 0.35, 0);
            wGroup.add(caliper);

            car.add(wGroup);
        });

        // 8. Dynamic Neon Underglow
        const underglowGeo = new THREE.PlaneGeometry(5.2, 9.6);
        const underglowMat = new THREE.MeshBasicMaterial({
            color: bodyColorHex,
            transparent: true,
            opacity: 0.65,
            side: THREE.DoubleSide
        });
        const underglow = new THREE.Mesh(underglowGeo, underglowMat);
        underglow.rotation.x = -Math.PI / 2;
        underglow.position.y = 0.12;
        car.add(underglow);
        car.userData.underglow = underglow;

        // 9. OVERHEAD BILLBOARD UI (Inspired by Nargor/car-action Overhead Billboard UI System)
        const billboard = this.createSupercarBillboard(nameLabel, subLabel, bodyColorHex);
        billboard.position.set(0, 6.2, 0);
        car.add(billboard);

        return car;
    }

    /* --------------------------------------------------------------------------
       10E-3. CREATE OVERHEAD BILLBOARD UI FOR SUPERCAR
       -------------------------------------------------------------------------- */
    createSupercarBillboard(title, sub, colorHex) {
        const canvas = document.createElement('canvas');
        canvas.width = 512;
        canvas.height = 140;
        const ctx = canvas.getContext('2d');

        ctx.fillStyle = 'rgba(10, 15, 30, 0.88)';
        ctx.roundRect(8, 8, 496, 124, 16);
        ctx.fill();

        ctx.strokeStyle = `#${colorHex.toString(16).padStart(6, '0')}`;
        ctx.lineWidth = 4;
        ctx.roundRect(8, 8, 496, 124, 16);
        ctx.stroke();

        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 26px "Segoe UI", Arial, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(title, 256, 50);

        ctx.fillStyle = `#${colorHex.toString(16).padStart(6, '0')}`;
        ctx.font = '600 17px "Segoe UI", Arial, sans-serif';
        ctx.fillText(sub, 256, 88);

        ctx.fillStyle = 'rgba(255, 255, 255, 0.15)';
        ctx.roundRect(130, 98, 252, 24, 6);
        ctx.fill();
        ctx.fillStyle = '#f8fafc';
        ctx.font = 'bold 12px "Segoe UI", monospace';
        ctx.fillText('[E / F] NỔ MÁY & REV NITRO BOOST', 256, 115);

        const tex = new THREE.CanvasTexture(canvas);
        const mat = new THREE.SpriteMaterial({ map: tex, transparent: true });
        const sprite = new THREE.Sprite(mat);
        sprite.scale.set(18, 5.0, 1);
        return sprite;
    }

    /* --------------------------------------------------------------------------
       10E-4. TRIGGER SUPERCAR REV & NITRO BOOST
       -------------------------------------------------------------------------- */
    triggerSupercarRev(car) {
        this.playSfx('turbo');
        if (car.group && car.group.userData && car.group.userData.exhaustGroup) {
            car.group.userData.exhaustGroup.scale.set(1.5, 1.5, 2.2);
            setTimeout(() => {
                if (car.group.userData.exhaustGroup) {
                    car.group.userData.exhaustGroup.scale.set(1.0, 1.0, 1.0);
                }
            }, 650);
        }
        const banner = document.getElementById('wingFocusBanner');
        const bannerText = document.getElementById('wingFocusBannerText');
        if (banner && bannerText) {
            bannerText.textContent = `🔥 [NITRO REV] ${car.name} V8/V12 gầm rú! Sẵn sàng đua TikTok Live!`;
            banner.style.display = 'block';
            setTimeout(() => { banner.style.display = 'none'; }, 3000);
        }
    }

    /* --------------------------------------------------------------------------
       10F. BUILD EXECUTIVE ASSISTANT ASTRA WORKSTATION (HQ RECEPTION CO-PILOT)
       -------------------------------------------------------------------------- */
    buildExecutiveAssistantAstra() {
        const deskGroup = new THREE.Group();
        // Positioned in the Executive Foyer outside the CEO Suite entrance
        deskGroup.position.set(-52, 3.75, -55);

        // 1. Curved Glass & Titanium Secretary Desk
        const deskGeo = new THREE.CylinderGeometry(8.5, 8.5, 3.2, 24, 1, false, 0, Math.PI * 0.85);
        const deskMat = new THREE.MeshStandardMaterial({
            color: 0x0f172a,
            metalness: 0.9,
            roughness: 0.15,
            side: THREE.DoubleSide
        });
        const deskMesh = new THREE.Mesh(deskGeo, deskMat);
        deskMesh.position.y = 1.6;
        deskMesh.rotation.y = Math.PI * 0.6;
        deskGroup.add(deskMesh);

        // Gold LED Desk Countertop Trim
        const rimGeo = new THREE.TorusGeometry(8.6, 0.12, 6, 24, Math.PI * 0.85);
        const rim = new THREE.Mesh(rimGeo, new THREE.MeshBasicMaterial({ color: 0xf59e0b }));
        rim.rotation.x = Math.PI / 2;
        rim.rotation.z = -Math.PI * 0.35;
        rim.position.y = 3.2;
        deskGroup.add(rim);

        // 2. Dual Curved Holographic Displays
        const screenGeo = new THREE.BoxGeometry(4.8, 2.6, 0.15);
        const leftScreen = new THREE.Mesh(screenGeo, new THREE.MeshStandardMaterial({
            color: 0x020617,
            emissive: 0x38bdf8,
            emissiveIntensity: 0.6,
            map: this.createTradingChartTexture(0x38bdf8)
        }));
        leftScreen.position.set(-2.5, 4.6, 1.2);
        leftScreen.rotation.y = 0.35;
        deskGroup.add(leftScreen);

        const rightScreen = new THREE.Mesh(screenGeo, new THREE.MeshStandardMaterial({
            color: 0x020617,
            emissive: 0xc084fc,
            emissiveIntensity: 0.6,
            map: this.createTradingChartTexture(0xc084fc)
        }));
        rightScreen.position.set(2.5, 4.6, 1.2);
        rightScreen.rotation.y = -0.35;
        deskGroup.add(rightScreen);

        // 3. 3D Floating Nameplate
        const nameplate = this.createHoloSprite('👑 THƯ KÝ TRƯỞNG ASTRA · AI CO-PILOT', 0xc084fc);
        nameplate.position.set(0, 7.2, 1.5);
        nameplate.scale.set(20, 4.0, 1);
        deskGroup.add(nameplate);

        // 4. Resident Astra Secretary Avatar seated behind desk
        const astraAvatar = this.createAstra3DModel();
        astraAvatar.position.set(0, 1.8, -2.5);
        astraAvatar.rotation.y = 0;
        deskGroup.add(astraAvatar);
        this.deskAstraAvatar = astraAvatar;

        // Register for station click & hovering
        deskMesh.userData = { deptKey: 'lead_pm', isAstraDesk: true };
        this.stationMeshes.push(deskMesh);

        this.scene.add(deskGroup);
    }

    /* --------------------------------------------------------------------------
       10G. BUILD FIRST-PERSON VIEW (FPV) CYBER COMPANION ASTRA
       -------------------------------------------------------------------------- */
    buildFpvCompanionAstra() {
        // Attached directly to this.camera so she moves seamlessly with the player!
        const fpvGroup = new THREE.Group();
        // Positioned comfortably in the bottom-right viewport (doesn't obstruct reticle)
        fpvGroup.position.set(1.45, -0.72, -2.5);
        fpvGroup.scale.set(0.38, 0.38, 0.38);

        // 1. Chibi Cyber Anime Head
        const skinMat = new THREE.MeshStandardMaterial({ color: 0xffe4d6, roughness: 0.4 });
        const hairMat = new THREE.MeshStandardMaterial({ color: 0xf472b6, roughness: 0.3, emissive: 0xec4899, emissiveIntensity: 0.2 });
        const goldMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.9, roughness: 0.2 });
        const cyanMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff });
        const whiteMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.2 });

        const head = new THREE.Mesh(new THREE.BoxGeometry(1.6, 1.5, 1.5), skinMat);
        head.position.y = 1.6;
        fpvGroup.add(head);

        // Hair Cap
        const hair = new THREE.Mesh(new THREE.BoxGeometry(1.75, 0.8, 1.65), hairMat);
        hair.position.set(0, 2.1, -0.05);
        fpvGroup.add(hair);

        // Twin-tails
        const leftTail = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.35, 1.8, 6), hairMat);
        leftTail.position.set(-1.1, 1.3, -0.2);
        leftTail.rotation.z = 0.35;
        fpvGroup.add(leftTail);
        this.fpvLeftTail = leftTail;

        const rightTail = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.35, 1.8, 6), hairMat);
        rightTail.position.set(1.1, 1.3, -0.2);
        rightTail.rotation.z = -0.35;
        fpvGroup.add(rightTail);
        this.fpvRightTail = rightTail;

        // Animated LED Visor Eyes (Cyan Glow)
        const eyeVisor = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.32, 0.2), cyanMat);
        eyeVisor.position.set(0, 1.6, 0.8);
        fpvGroup.add(eyeVisor);
        this.fpvCompanionEyeVisor = eyeVisor;

        // Cute Blush Cheeks
        for (let b = -1; b <= 1; b += 2) {
            const blush = new THREE.Mesh(new THREE.PlaneGeometry(0.24, 0.12), new THREE.MeshBasicMaterial({ color: 0xff0077 }));
            blush.position.set(b * 0.55, 1.35, 0.82);
            fpvGroup.add(blush);
        }

        // 2. Cyber Suit Body
        const torso = new THREE.Mesh(new THREE.BoxGeometry(1.2, 1.5, 0.9), whiteMat);
        torso.position.y = 0.35;
        fpvGroup.add(torso);

        // Glowing Heart Core
        const core = new THREE.Mesh(new THREE.SphereGeometry(0.25, 12, 12), cyanMat);
        core.position.set(0, 0.45, 0.5);
        fpvGroup.add(core);

        // Skirt Ring
        const skirt = new THREE.Mesh(new THREE.TorusGeometry(0.85, 0.08, 6, 16), hairMat);
        skirt.rotation.x = Math.PI / 2;
        skirt.position.y = -0.4;
        fpvGroup.add(skirt);

        // 3. Fluttering Crystal Holographic Wings
        const wingMat = new THREE.MeshBasicMaterial({
            color: 0x38bdf8,
            transparent: true,
            opacity: 0.75,
            side: THREE.DoubleSide
        });
        const leftWing = new THREE.Mesh(new THREE.ConeGeometry(0.3, 1.8, 4), wingMat);
        leftWing.position.set(-0.8, 0.6, -0.6);
        leftWing.rotation.z = 0.75;
        fpvGroup.add(leftWing);
        this.fpvLeftWing = leftWing;

        const rightWing = new THREE.Mesh(new THREE.ConeGeometry(0.3, 1.8, 4), wingMat);
        rightWing.position.set(0.8, 0.6, -0.6);
        rightWing.rotation.z = -0.75;
        fpvGroup.add(rightWing);
        this.fpvRightWing = rightWing;

        // 4. Rotating Bitcoin Halo Ring
        const halo = new THREE.Mesh(new THREE.TorusGeometry(0.7, 0.08, 8, 20), goldMat);
        halo.position.set(0, 2.7, 0);
        halo.rotation.x = Math.PI / 2.3;
        fpvGroup.add(halo);
        this.fpvHalo = halo;

        // 5. Mini Holographic Live Data Tablet in hands
        const tabletGeo = new THREE.BoxGeometry(1.4, 0.9, 0.06);
        const tabletMat = new THREE.MeshStandardMaterial({
            color: 0x050c18,
            emissive: 0x00f0ff,
            emissiveIntensity: 0.7,
            map: this.createTradingChartTexture(0x10b981)
        });
        const tablet = new THREE.Mesh(tabletGeo, tabletMat);
        tablet.position.set(0, 0.1, 0.9);
        tablet.rotation.x = -0.35;
        fpvGroup.add(tablet);

        // 6. Overhead Hologram Name Tag
        const badge = this.createHoloSprite('🤖 ASTRA CO-PILOT [E: Chat]', 0xc084fc);
        badge.position.set(0, 3.4, 0);
        badge.scale.set(6.5, 1.6, 1);
        fpvGroup.add(badge);

        // Default hidden until cameraMode === 'fpv'
        fpvGroup.visible = false;
        this.camera.add(fpvGroup);
        this.fpvCompanionGroup = fpvGroup;
    }

    /* --------------------------------------------------------------------------
       10H. ANIMATE MEGACITY SKYLINE, SUPERCARS & COMPANIONS
       -------------------------------------------------------------------------- */
    animateMegacityAndCompanion(time, delta) {
        // 1. Skyline Aviation Beacons Flashing
        if (this.skylineBeacons && this.skylineBeacons.length > 0) {
            this.skylineBeacons.forEach(b => {
                const flash = Math.sin(time * 5.0 + b.phase);
                b.mesh.visible = flash > 0.15;
            });
        }

        // 2. Air Traffic Sky-Cruisers Gliding
        if (this.skyCruisers && this.skyCruisers.length > 0) {
            this.skyCruisers.forEach(c => {
                c.userData.angle += delta * c.userData.speed;
                const a = c.userData.angle;
                const r = c.userData.radius;
                c.position.x = Math.sin(a) * r;
                c.position.z = Math.cos(a) * r;
                c.position.y = c.userData.baseY + Math.sin(time * 2.0 + a) * 3.5;
                c.rotation.y = a + Math.PI / 2;
            });
        }

        // 3. Supercars Underglow & Flame Exhausts Pulse
        if (this.supercars && this.supercars.length > 0) {
            this.supercars.forEach(sc => {
                if (sc.group.userData.underglow) {
                    sc.group.userData.underglow.material.opacity = 0.55 + Math.sin(time * 4.0) * 0.25;
                }
            });

            // Check distance to Boss for Supercar Proximity Prompt
            let nearCar = null;
            for (let i = 0; i < this.supercars.length; i++) {
                const sc = this.supercars[i];
                if (this.bossPosition.distanceTo(sc.worldPos) < 14) {
                    nearCar = sc;
                    break;
                }
            }
            this.nearbySupercar = nearCar;
        }

        // 4. Resident HQ Astra Desk Avatar Animation
        if (this.deskAstraAvatar && this.deskAstraAvatar.userData && this.deskAstraAvatar.userData.animate) {
            this.deskAstraAvatar.userData.animate(time, delta);
        }

        // 5. First-Person View (FPV) Companion Astra Animation
        if (this.fpvCompanionGroup && this.fpvCompanionGroup.visible) {
            const bobY = Math.sin(time * 3.5) * 0.05;
            const tiltZ = Math.sin(time * 2.2) * 0.04;
            this.fpvCompanionGroup.position.y = -0.72 + bobY;
            this.fpvCompanionGroup.rotation.z = tiltZ;
            this.fpvCompanionGroup.rotation.y = -0.22 + Math.sin(time * 1.5) * 0.05;

            if (this.fpvLeftWing && this.fpvRightWing) {
                const wingFlap = Math.sin(time * 18.0) * 0.35;
                this.fpvLeftWing.rotation.y = wingFlap;
                this.fpvRightWing.rotation.y = -wingFlap;
            }

            if (this.fpvLeftTail && this.fpvRightTail) {
                const hBounce = Math.sin(time * 4.0) * 0.12;
                this.fpvLeftTail.rotation.z = 0.35 + hBounce;
                this.fpvRightTail.rotation.z = -0.35 - hBounce;
            }

            if (this.fpvHalo) {
                this.fpvHalo.rotation.y += delta * 2.0;
            }

            if (this.fpvCompanionEyeVisor) {
                const blink = Math.sin(time * 0.8);
                this.fpvCompanionEyeVisor.scale.y = (blink > 0.96) ? 0.1 : 1.0;
            }
        }
    }"""

if old_avatars_target in text:
    text = text.replace(old_avatars_target, new_avatars_methods, 1)
    print("5. Added 3D builder methods after buildAvatars successfully.")
else:
    print("WARNING: Could not find old_avatars_target")

# 6. KeyF / KeyE: Add supercar rev & FPV Astra quick chat
old_key_target = """            // [F / E] Interact with nearby agent, aimed station, or hovered station
            if (code === 'KeyF' || keyLower === 'f' || keyLower === 'e') {
                if (this.nearbyAgentDept) {
                    e.preventDefault();
                    window.openCyberIntercomForDept(this.nearbyAgentDept);
                    return;
                } else if (this.aimHitDept) {
                    e.preventDefault();
                    this.onStationClick(this.aimHitDept);
                    return;
                } else if (this.hoveredDept) {
                    e.preventDefault();
                    this.onStationClick(this.hoveredDept);
                    return;
                }
            }"""

new_key_replacement = """            // [F / E] Interact with nearby agent, supercar, aimed station, or FPV Astra
            if (code === 'KeyF' || keyLower === 'f' || keyLower === 'e') {
                if (this.nearbySupercar) {
                    e.preventDefault();
                    this.triggerSupercarRev(this.nearbySupercar);
                    return;
                } else if (this.nearbyAgentDept) {
                    e.preventDefault();
                    window.openCyberIntercomForDept(this.nearbyAgentDept);
                    return;
                } else if (this.aimHitDept) {
                    e.preventDefault();
                    this.onStationClick(this.aimHitDept);
                    return;
                } else if (this.hoveredDept) {
                    e.preventDefault();
                    this.onStationClick(this.hoveredDept);
                    return;
                } else if (this.cameraMode === 'fpv') {
                    // In FPV mode, pressing E/F opens quick dialogue with Astra
                    e.preventDefault();
                    window.openCyberIntercomForDept('lead_pm');
                    return;
                }
            }"""

if old_key_target in text:
    text = text.replace(old_key_target, new_key_replacement, 1)
    print("6. Enhanced KeyF / KeyE handling successfully.")
else:
    print("WARNING: Could not find old_key_target")

# 7. setCameraMode: toggle FPV companion visibility & world companion visibility
old_cam_target = """        // Update active UI tool buttons
        const btnMap = {"""

new_cam_replacement = """        // Toggle FPV Companion visibility
        if (this.fpvCompanionGroup) {
            this.fpvCompanionGroup.visible = (mode === 'fpv');
        }
        if (this.astraModel) {
            this.astraModel.visible = (mode !== 'fpv');
            if (this.astraShadow) this.astraShadow.visible = (mode !== 'fpv');
        }

        // Update active UI tool buttons
        const btnMap = {"""

if old_cam_target in text:
    text = text.replace(old_cam_target, new_cam_replacement, 1)
    print("7. Added camera mode hooks for FPV companion successfully.")
else:
    print("WARNING: Could not find old_cam_target")

# 8. animate loop: adjust Astra follow offset to front-right & call animateMegacityAndCompanion
old_astra_offset = """        // Astra Companion following Boss (With synced elevation & parkour jumps)
        const astraOffset = new THREE.Vector3(
            Math.sin(this.bossHeading + 2.2) * 5.5,
            0,
            Math.cos(this.bossHeading + 2.2) * 5.5
        );"""

new_astra_offset = """        // Astra Companion following Boss (Positioned at right side +0.82 rads, visible in TPP)
        const astraOffset = new THREE.Vector3(
            Math.sin(this.bossHeading + 0.82) * 5.2,
            0,
            Math.cos(this.bossHeading + 0.82) * 5.2
        );"""

if old_astra_offset in text:
    text = text.replace(old_astra_offset, new_astra_offset, 1)
    print("8A. Adjusted Astra follow offset to front-right successfully.")
else:
    print("WARNING: Could not find old_astra_offset")

old_render_target = """        // Render Scene
        if (this.renderer && this.scene && this.camera) {
            this.renderer.render(this.scene, this.camera);
        }"""

new_render_replacement = """        // Animate Megacity Skyline, Supercars & FPV Companion
        if (this.animateMegacityAndCompanion) {
            this.animateMegacityAndCompanion(time, delta);
        }

        // Render Scene
        if (this.renderer && this.scene && this.camera) {
            this.renderer.render(this.scene, this.camera);
        }"""

if old_render_target in text:
    text = text.replace(old_render_target, new_render_replacement, 1)
    print("8B. Added animateMegacityAndCompanion call before render successfully.")
else:
    print("WARNING: Could not find old_render_target")

# 9. openCyberIntercomModal: exit pointer lock and auto-focus input
old_intercom_target = """window.openCyberIntercomModal = function(agentName = 'Astra') {
    const modal = document.getElementById('cyber-intercom-modal');
    if (!modal) return;
    window.currentIntercomAgent = agentName;
    modal.style.display = 'flex';"""

new_intercom_replacement = """window.openCyberIntercomModal = function(agentName = 'Astra') {
    const modal = document.getElementById('cyber-intercom-modal');
    if (!modal) return;
    if (document.pointerLockElement) {
        document.exitPointerLock();
    }
    window.currentIntercomAgent = agentName;
    modal.style.display = 'flex';
    const input = document.getElementById('intercom-user-input');
    if (input) {
        setTimeout(() => input.focus(), 60);
    }"""

if old_intercom_target in text:
    text = text.replace(old_intercom_target, new_intercom_replacement, 1)
    print("9. Enhanced openCyberIntercomModal with exitPointerLock & auto-focus successfully.")
else:
    print("WARNING: Could not find old_intercom_target")

with open(target_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Finished applying all patches to", target_path)
