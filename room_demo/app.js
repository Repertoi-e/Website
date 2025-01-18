import * as THREE from 'three';

import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const textureLoader = new THREE.TextureLoader();
const cubeTextureLoader = new THREE.CubeTextureLoader();

var scene = new THREE.Scene();
var camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
var renderer = new THREE.WebGLRenderer({ antialias: true });

const viewport = document.querySelector("#viewport");

var controls = new OrbitControls(camera, viewport);
controls.enableDamping = true;
controls.dampingFactor = 0.25;
controls.enableZoom = true;
controls.enablePan = true;
controls.enableRotate = true;
controls.enabled = false;

var draggingControlsEnabled = true;

setupScene();

function setupScene() {
    renderer.setClearColor("#000000");
    renderer.setSize(window.innerWidth, window.innerHeight);

    document.body.appendChild(renderer.domElement);

    // add ambient light
    const ambientLight = new THREE.AmbientLight(0xffffff, 150000);
    scene.add(ambientLight);

    scene.add(camera);

    loadHotspots();
}

viewport.addEventListener("pointerdown", (event) => {});

var hotspots = [];
var cubemapVariants = {};

var startPosition;
var startHotspot;

var targetHotspot;
var targetPosition;

var averageHotspotPosition = new THREE.Vector3();

var uniformBlends;

function loadHotspots() {
    let texturePromises = [];
    $.get('./Tour/Hotspots.txt', (data) => {
        let lines = data.split('\n');
        lines.forEach((line) => {
            const parts = line.split(' ');

            let id = parts[0];
            const position = new THREE.Vector3();
            parts.forEach((part) => {
                if (part.startsWith('X=')) {
                    position.x = parseFloat(part.substring(2));
                } else if (part.startsWith('Y=')) {
                    position.y = parseFloat(part.substring(2));
                } else if (part.startsWith('Z=')) {
                    position.z = parseFloat(part.substring(2));
                }
            });
            position.applyAxisAngle(new THREE.Vector3(1, 0, 0), -Math.PI / 2); // Flip y and z

            averageHotspotPosition.add(position);

            let hotspot = {
                position,
                texturePath: `./Tour/Panoramas/individual/Byt205_${id}`,
            };

            let cubemapPromise = new Promise((resolve) => {
                let variants = [hotspot.texturePath];
                if (id == "01") {
                    variants = ['', '_base_floor.png', '_darker_floor.png', '_lighter_floor.png', '_base_sofa.png', '_blue_sofa.png', '_pink_sofa.png'].map((x) => { return hotspot.texturePath + x; });
                }
                let variantsLoaded = 1;
                hotspot.cubemap = cubeTextureLoader.load([
                    variants[0] + '.jpg_pX.jpg',
                    variants[0] + '.jpg_nX.jpg',
                    variants[0] + '.jpg_pY.jpg',
                    variants[0] + '.jpg_nY.jpg',
                    variants[0] + '.jpg_pZ.jpg',
                    variants[0] + '.jpg_nZ.jpg'
                ], () => {
                    if (variants.length == 1) { resolve(); return; }

                    for (let i = 1; i < variants.length; i++) {
                        if (!(id in cubemapVariants)) {
                            cubemapVariants[id] = [];
                        }
                        cubemapVariants[id].push(
                            cubeTextureLoader.load([
                                variants[i] + '_pX.png',
                                variants[i] + '_nX.png',
                                variants[i] + '_pY.png',
                                variants[i] + '_nY.png',
                                variants[i] + '_pZ.png',
                                variants[i] + '_nZ.png'
                            ], () => {
                                variantsLoaded += 1;
                                if (variantsLoaded == variants.length) {
                                    resolve();
                                }
                            }
                            )
                        );
                    }
                });
            });
            texturePromises.push(cubemapPromise);

            hotspots.push(hotspot);
        });

        const urlParams = new URLSearchParams(window.location.search);

        var initialQuaternion = null;

        const quaternionString = urlParams.get("quaternion");
        if (quaternionString) {
            const quaternionArray = quaternionString.split(",").map(Number);
            if (quaternionArray.length === 4) {
                initialQuaternion = new THREE.Quaternion().fromArray(quaternionArray);
                console.log("Loaded camera rotation from URL:", camera.quaternion);
            }
        }

        var initialHotspot = 0;

        const index = urlParams.get("index");
        if (index !== null) {
            console.log("Loaded index from URL:", index);
            initialHotspot = parseInt(index);
        }

        Promise.all(texturePromises).then(() => {
            if (hotspots.length > 0) {
                averageHotspotPosition.divideScalar(hotspots.length);
                controls.target = averageHotspotPosition;

                uniformBlends = hotspots.map((_) => { return 1 / hotspots.length; });

                const pointLight = new THREE.PointLight(0xffffff, 15);
                pointLight.position.copy(averageHotspotPosition);
                scene.add(pointLight);

                camera.position.copy(hotspots[initialHotspot].position);

                if (initialQuaternion) {
                    camera.quaternion.copy(initialQuaternion);
                }

                const rotation = new THREE.Euler().setFromQuaternion(camera.quaternion.clone(), 'YXZ'); // Use 'YXZ' to avoid gimbal lock
                pitch = Math.asin(Math.sin(rotation.x));
                yaw = rotation.y;

                startPosition = camera.position.clone();
                startHotspot = hotspots[initialHotspot];

                targetHotspot = hotspots[initialHotspot];
                targetPosition = camera.position.clone();

                setupMaterial();
            }
            console.log(hotspots.length + " hotspots loaded");
        });
    });
}

export function setSofaColor(color) {
    if (color == "0") {
        material.uniforms.variantTexture2.value = null;
    } else {
        material.uniforms.variantTexture2.value = cubemapVariants['01'][3 + parseInt(color)];
    }
}

export function setFloorColor(color) {
    if (color == "0") {
        material.uniforms.variantTexture1.value = null;
    } else {
        material.uniforms.variantTexture1.value = cubemapVariants['01'][parseInt(color)];
    }
}

export async function screenshot() {
    if (!renderer || !scene || !camera) {
        console.error("Three.js renderer, scene, or camera is missing!");
        return;
    }

    renderer.render(scene, camera);

    const canvas = renderer.domElement;
    canvas.toBlob(async (blob) => {
        if (blob) {
            try {
                await navigator.clipboard.write([
                    new ClipboardItem({ "image/png": blob }),
                ]);
                console.log("Screenshot copied to clipboard!");
            } catch (err) {
                console.error("Failed to copy screenshot:", err);
            }
        }
    }, "image/png");
};

function findClosestHotspot() {
    let closestHotspot = null;
    let closestDistance = Infinity;

    hotspots.forEach((hotspot) => {
        const distance = camera.position.distanceTo(hotspot.position);
        if (distance < closestDistance) {
            closestDistance = distance;
            closestHotspot = hotspot;
        }
    });

    return closestHotspot;
}

var material = null;
var room = null;

function setupMaterial() {
    const vertexShader = `
    varying vec3 vWorldPosition;

    void main() {
        vWorldPosition = (modelMatrix * vec4(position, 1.0)).xyz;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
    `;

    const fragmentShader = `
    uniform samplerCube panoramicTextures[${hotspots.length}]; 

    uniform samplerCube variantTexture1;
    uniform samplerCube variantTexture2;

    uniform vec3 hotspotPositions[${hotspots.length}]; 
    uniform float blendFactors[${hotspots.length}];

    varying vec3 vWorldPosition;

    const float PI = 3.1415926535897932384626433832795;

    void main() {
        vec4 finalColor = vec4(0.0);

        ${hotspots.map((_, i) => `
        {
            vec3 direction = normalize(vWorldPosition - hotspotPositions[${i}]);
            direction = vec3(-direction.z, direction.y, direction.x);
            vec4 color = textureCube(panoramicTextures[${i}], direction);

            vec4 variantColor1 = textureCube(variantTexture1, direction);
            float alpha = variantColor1.a;
            color = mix(color, variantColor1, alpha);

            vec4 variantColor2 = textureCube(variantTexture2, direction);
            alpha = variantColor2.a;
            color = mix(color, variantColor2, alpha);

            finalColor += color * blendFactors[${i}];
        }
        `).join('')}

        gl_FragColor = finalColor;
    }
    `;

    material = new THREE.ShaderMaterial({
        uniforms: {
            panoramicTextures: { value: hotspots.map((hotspot) => hotspot.cubemap) },
            hotspotPositions: { value: hotspots.map((hotspot) => hotspot.position) },
            variantTexture1: { value: null },
            variantTexture2: { value: null },
            blendFactors: { value: hotspots.map(() => 0.0) },
        },
        vertexShader,
        fragmentShader,
        side: THREE.FrontSide
    });

    const loader = new OBJLoader();
    loader.load(
        './Tour/lowpoly.obj',
        (object) => {
            scene.add(object);

            // Assuming 'object' is your loaded mesh
            object.traverse(function (child) {
                if (child instanceof THREE.Mesh) {
                    child.material = material;
                    child.name = 'ROOM';
                }
            });
            object.rotation.x = -Math.PI / 2; // Flip y and z

            room = object;
        },
        undefined,
        (error) => console.error('Error loading room:', error)
    );

    render(1)
}

var isDragging = false;
var previousMousePosition = { x: 0, y: 0 };

const rotationSpeed = 0.002;

var mouseDownFrames = 0;

viewport.addEventListener('mousedown', (event) => {
    if (draggingControlsEnabled) {
        previousMousePosition = { x: event.clientX, y: event.clientY };
        isDragging = true;
        mouseDownFrames = 0;
    }
});

viewport.addEventListener('mouseup', () => {
    isDragging = false;
    if (draggingControlsEnabled) {
        if (mouseDownFrames < 5) {
            moveInDirection(intersectionPoint.clone().sub(camera.position).normalize());
        }
    }
});

var framesSinceChangeHotspot = 0;

export var movementSpeed = 0.036;
export function setMovementSpeed(speed) { movementSpeed = speed; }

export var movementDelay = 40;
export function setMovementDelay(delay) { movementDelay = delay; }

function moveInDirection(direction) {
    if (framesSinceChangeHotspot < movementDelay) {
        return;
    }

    framesSinceChangeHotspot = 0;

    if (direction) {
        let nextHotspot = null;
        let closestDistance = Infinity;

        hotspots.forEach((hotspot) => {
            if (hotspot === targetHotspot) {
                return;
            }

            const toHotspot = hotspot.position.clone().sub(camera.position);
            const dotProduct = toHotspot.normalize().dot(direction);

            if (dotProduct > 0.7) {
                const distance = camera.position.distanceTo(hotspot.position);
                if (distance < closestDistance) {
                    const raycaster = new THREE.Raycaster(camera.position, toHotspot.normalize(), 0, distance);
                    const intersects = raycaster.intersectObjects(scene.children, true);
                    if (intersects.length > 0) {
                        if (intersects[0].object.name === 'ROOM') {
                            console.log('Room in the way');
                            return;
                        }
                    }

                    closestDistance = distance;
                    nextHotspot = hotspot;
                }
            }
        });

        if (nextHotspot) {
            startPosition.copy(camera.position);
            startHotspot = findClosestHotspot();

            if (targetHotspot !== nextHotspot) {
                targetHotspot = nextHotspot;
            }
            targetPosition.copy(nextHotspot.position);
        }
    }
}

window.addEventListener('keydown', (event) => {
    let direction = null;
    switch (event.key) {
        case 'w':
            direction = new THREE.Vector3(0, 0, -1);
            break;
        case 's':
            direction = new THREE.Vector3(0, 0, 1);
            break;
        case 'a':
            direction = new THREE.Vector3(-1, 0, 0);
            break;
        case 'd':
            direction = new THREE.Vector3(1, 0, 0);
            break;
    }
    if (direction) {
        direction.applyQuaternion(camera.quaternion);
        direction.normalize();
        moveInDirection(direction);
    }
});

var pitch = 0;
var yaw = 0;

var MAX_PITCH = Math.PI / 2;

var raycaster = new THREE.Raycaster();
var mouse = new THREE.Vector2();

var intersectionPoint = new THREE.Vector3();

viewport.addEventListener('mousemove', (event) => {
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

    if (isDragging && draggingControlsEnabled && !isInDollHouse) {
        const deltaX = event.clientX - previousMousePosition.x;
        const deltaY = event.clientY - previousMousePosition.y;

        yaw += deltaX * rotationSpeed;
        if (yaw > Math.PI * 2) {
            yaw -= Math.PI * 2;
        } else if (yaw < -Math.PI * 2) {
            yaw += Math.PI * 2;
        }

        pitch += deltaY * rotationSpeed;
        pitch = Math.max(-MAX_PITCH, Math.min(MAX_PITCH, pitch));

        const horizontalQuaternion = new THREE.Quaternion().setFromAxisAngle(
            new THREE.Vector3(0, 1, 0),
            yaw
        );
        const verticalQuaternion = new THREE.Quaternion().setFromAxisAngle(
            new THREE.Vector3(1, 0, 0),
            pitch
        );

        const cameraQuaternion = new THREE.Quaternion();
        cameraQuaternion.multiply(horizontalQuaternion).multiply(verticalQuaternion);
        camera.quaternion.copy(cameraQuaternion);

        previousMousePosition = { x: event.clientX, y: event.clientY };
    }
});

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

let disk = null;
const diskMaterial = new THREE.MeshBasicMaterial({
    color: 0x063970,
    side: THREE.DoubleSide,
    transparent: true, // Important for renderOrder to work reliably
    opacity: 0.50, // Avoid full opacity which can cause issues
    depthWrite: false, // Prevents z-fighting with the object it sits on
    depthTest: false,
    polygonOffset: true,
    polygonOffsetFactor: -1, // Adjust as needed
    polygonOffsetUnits: -1,
});

const diskGeometry = new THREE.CircleGeometry(0.1, 32);
disk = new THREE.Mesh(diskGeometry, diskMaterial);
scene.add(disk);

function updateRaycast() {
    raycaster.setFromCamera(mouse, camera);

    const intersects = raycaster.intersectObjects(scene.children, true); // Check all children, including within loaded objects

    if (intersects.length > 0) {

        let meshIntersection = null;
        for (let i = 0; i < intersects.length; i++) {
            if (intersects[i].object instanceof THREE.Mesh) {
                if (intersects[i].object.name === 'ROOM') {
                    meshIntersection = intersects[i];
                    break;
                }
            }
        }

        if (meshIntersection) {
            let intersectedFace = meshIntersection.face;
            intersectionPoint.copy(meshIntersection.point);

            const faceNormal = intersectedFace.normal.clone().transformDirection(meshIntersection.object.matrixWorld); // Important: Transform normal to world space
            const faceCenter = intersectionPoint;

            disk.position.copy(faceCenter);
            disk.lookAt(faceCenter.clone().add(faceNormal));
        } else {
            disk.position.set(-1000000, 0, -1000000);
            intersectionPoint.copy(-1000000, 0, -1000000);
        }
    } else {
        disk.position.set(-1000000, 0, -1000000);
        intersectionPoint.copy(-1000000, 0, -1000000);
    }
}

export function goHome() {
    console.log('Going home');
}

var isDay = true;

export function toggleDayNight() {
    isDay = !isDay;
    room.traverse((child) => {
        if (child instanceof THREE.Mesh) {
            child.material = isDay
                ? new THREE.MeshPhongMaterial({ color: 0x00ff00, shininess: 30 })
                : material;
        }
    });

    console.log('Toggling day/night');
}

export function startMeasure() {
    console.log('Starting measure');
}

export function saveCameraAndIndexToURL() {
    console.log("awgaw  ");
    const index = hotspots.indexOf(targetHotspot);

    const { x, y, z, w } = camera.quaternion;
    const quaternionString = `${x.toFixed(6)},${y.toFixed(6)},${z.toFixed(6)},${w.toFixed(6)}`;
    const newURL = `${window.location.origin}${window.location.pathname}?quaternion=${quaternionString}&index=${index}`;

    window.history.replaceState(null, "", newURL);

    console.log("Sharable URL:", newURL);
    return newURL; // Optional: return for copying
}

var isInDollHouse = false;

var houseBlendFactor = 0.0;
var targetHouseBlendFactor = 0.0;

export function toggleDollhouseView() {
    isInDollHouse = !isInDollHouse;

    if (isInDollHouse) {
        if (window.currentTween) {
            window.currentTween.kill();
        }

        disk.position.set(-1000000, 0, -1000000);

        const backwardDirection = new THREE.Vector3(0, 0, 1).applyQuaternion(camera.quaternion);
        const thirdPersonPosition = averageHotspotPosition.clone().add(backwardDirection.clone().multiplyScalar(10));

        console.log(backwardDirection.clone());
        controls.target = camera.position.clone().add(backwardDirection.clone().multiplyScalar(-1));

        let tween = gsap.to(camera.position, {
            x: thirdPersonPosition.x,
            y: thirdPersonPosition.y,
            z: thirdPersonPosition.z,
            duration: 0.8,
            ease: 'power2.out',
            onUpdate: () => {
                controls.update(); // Update controls to reflect position changes
            },
            onComplete: () => {
                controls.enabled = true;
            }
        });
        window.currentTween = tween;
        targetHouseBlendFactor = 1.0;

        draggingControlsEnabled = false;
    } else {
        if (window.currentTween) {
            window.currentTween.kill();
        }

        controls.enabled = false;

        let tween = gsap.to(camera.position, {
            x: targetPosition.x,
            y: targetPosition.y,
            z: targetPosition.z,
            duration: 0.8,
            ease: 'power2.out',
            onUpdate: () => {
                let cameraQuaternion = camera.quaternion;

                const rotation = new THREE.Euler().setFromQuaternion(cameraQuaternion, 'YXZ'); // Use 'YXZ' to avoid gimbal lock
                pitch = Math.asin(Math.sin(rotation.x));
                yaw = rotation.y;
            },
            onComplete: () => {
                draggingControlsEnabled = true;
            }
        });
        window.currentTween = tween;

        targetHouseBlendFactor = 0.0;
    }
}

var targetBlends;

var previousTime = 0;
function render(time) {
    const deltaTime = (time - previousTime) / 1000;
    previousTime = time;

    if (!isInDollHouse) {
        camera.position.lerp(targetPosition, movementSpeed);

        let w1 = 1 / Math.max(0.01, Math.pow(camera.position.distanceTo(startHotspot.position), 2));
        let w2 = 1 / Math.max(0.01, Math.pow(camera.position.distanceTo(targetHotspot.position), 2));

        let blendFactors = hotspots.map(() => 0.0);
        blendFactors[hotspots.indexOf(startHotspot)] = w1;
        blendFactors[hotspots.indexOf(targetHotspot)] = w2;

        let sum = blendFactors.reduce((a, b) => a + b, 0);
        targetBlends = blendFactors.map((v) => v / sum);

        /*
        hotspots.forEach((hotspot) => {
            const distance = camera.position.distanceTo(hotspot.position);
            const weight = 1 / Math.pow(distance, inversePowerDistance);
            totalWeight += weight;
        });

        hotspots.forEach((hotspot, i) => {
            const distance = camera.position.distanceTo(hotspot.position);
            const weight = 1 / Math.pow(distance, inversePowerDistance);
            material.uniforms.blendFactors.value[i] = weight / totalWeight;
        });*/

        /*
                if (startHotspot) {
                    material.uniforms.panoramicTexture.value = startHotspot.cubemap;
                    material.uniforms.hotspotPosition.value.copy(startHotspot.position);
                }
        
                if (targetHotspot) {
                    material.uniforms.targetPanoramicTexture.value = targetHotspot.cubemap;
                    material.uniforms.targetHotspotPosition.value.copy(targetHotspot.position);
                }
        
                const distanceToTarget = camera.position.distanceTo(targetHotspot.position);
                const totalDistance = startPosition.distanceTo(targetHotspot.position);
        
                var blendFactor = 1.0 - Math.max(0, Math.min(1, distanceToTarget / totalDistance));
                if (totalDistance < 0.01) {
                    blendFactor = 1.0;
                }
                material.uniforms.blendFactor.value = blendFactor;*/

    } else {
        controls.update();
    }

    updateRaycast();

    houseBlendFactor = THREE.MathUtils.lerp(houseBlendFactor, targetHouseBlendFactor, 0.1);
    material.uniforms.blendFactors.value = targetBlends.map((value, index) => (1 - houseBlendFactor) * value + (houseBlendFactor) * uniformBlends[index]);

    mouseDownFrames += 1;
    framesSinceChangeHotspot += 1;

    renderer.render(scene, camera);
    requestAnimationFrame(render);

}