import * as THREE from 'three';

import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';

var scene = new THREE.Scene();

let camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);

const pointLight = new THREE.PointLight(0xffffff, 15);
pointLight.position.set(0, 0, 15);
scene.add(pointLight);

scene.add(camera);

var renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setClearColor("#000000");

renderer.setSize(window.innerWidth, window.innerHeight);

document.body.appendChild(renderer.domElement);

const ambientLight = new THREE.AmbientLight(0xffffff);
scene.add(ambientLight);


const textureLoader = new THREE.TextureLoader();
const hotspots = [
    {
        position: new THREE.Vector3(-1.67552, 1.4, -1.82892), // Camera 1 position
        texture: 'Camera1.png',
        panoramicTexture: null
    },
    {
        position: new THREE.Vector3(-1.49854, 1.4, 3.06895), // Camera 2 position
        texture: 'Camera2.png',
        panoramicTexture: null
    },
    {
        position: new THREE.Vector3(1.08992, 1.4, -2.14032), // Camera 3 position
        texture: 'Camera3.png',
        panoramicTexture: null
    }
];

camera.position.copy(hotspots[0].position);

let texturesLoaded = 0;
// loop through hotspots and load textures
hotspots.forEach((hotspot) => {
    hotspot.panoramicTexture = textureLoader.load(hotspot.texture, () => {
        hotspot.panoramicTexture.mapping = THREE.EquirectangularReflectionMapping;
        hotspot.panoramicTexture.wrapS = THREE.RepeatWrapping;
        hotspot.panoramicTexture.wrapT = THREE.RepeatWrapping;
        hotspot.panoramicTexture.magFilter = THREE.LinearFilter;
        hotspot.panoramicTexture.minFilter = THREE.LinearFilter;

        texturesLoaded++;
        if (texturesLoaded === hotspots.length) {
            setupMaterial();
        }
    });
});

// make multiline string
const vertexShader = `
varying vec3 vWorldPosition;

void main() {
    vWorldPosition = (modelMatrix * vec4(position, 1.0)).xyz;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

const fragmentShader = `
uniform sampler2D panoramicTexture; // Current texture
uniform sampler2D targetPanoramicTexture; // Target texture
uniform vec3 hotspotPosition; // Current hotspot position
uniform vec3 targetHotspotPosition; // Target hotspot position
uniform float blendFactor; // Blending factor between 0.0 and 1.0

varying vec3 vWorldPosition;

const float PI = 3.1415926535897932384626433832795;

void main() {
    // Calculate direction vectors for current and target hotspots
    vec3 directionCurrent = normalize(vWorldPosition - hotspotPosition);
    vec3 directionTarget = normalize(vWorldPosition - targetHotspotPosition);

    // Compute UV for the current panoramic texture
    vec2 uvCurrent = vec2(
        0.5 + atan(directionCurrent.x, directionCurrent.z) / (2.0 * PI),
        1.0 - (0.5 - asin(directionCurrent.y) / PI) // Flip V coordinate
    );

    // Compute UV for the target panoramic texture
    vec2 uvTarget = vec2(
        0.5 + atan(directionTarget.x, directionTarget.z) / (2.0 * PI),
        1.0 - (0.5 - asin(directionTarget.y) / PI) // Flip V coordinate
    );

    // Sample both textures
    vec4 colorCurrent = texture2D(panoramicTexture, uvCurrent);
    vec4 colorTarget = texture2D(targetPanoramicTexture, uvTarget);

    // Blend between the two textures based on the blend factor
    vec4 finalColor = mix(colorCurrent, colorTarget, blendFactor);

    gl_FragColor = finalColor;
}
`;

let startPosition = camera.position.clone();
let startHotspot = hotspots[0];

let targetHotspot = hotspots[0];
let targetPosition = camera.position.clone();

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

function setupMaterial() {
    material = new THREE.ShaderMaterial({
        uniforms: {
            panoramicTexture: { value: hotspots[0].panoramicTexture },
            targetPanoramicTexture: { value: hotspots[0].panoramicTexture }, 
            hotspotPosition: { value: hotspots[0].position.clone() },
            targetHotspotPosition: { value: hotspots[0].position.clone() },
            blendFactor: { value: 0.0 }
        },
        vertexShader,
        fragmentShader,
        side: THREE.FrontSide
    });

    const loader = new OBJLoader();
    loader.load(
        'RoomTest.obj',
        (object) => {
            scene.add(object);
            object.position.set(0, 0, 0);
            object.scale.z = -1;

            // Assuming 'object' is your loaded mesh
            object.traverse(function (child) {
                if (child instanceof THREE.Mesh) {
                    child.material = material;
                }
            });
        },
        undefined,
        (error) => console.error('Error loading room:', error)
    );

    render(1)
}

let isDragging = false;
let previousMousePosition = { x: 0, y: 0 };

const rotationSpeed = 0.002;

document.addEventListener('mousedown', (event) => {
    isDragging = true;
    previousMousePosition = { x: event.clientX, y: event.clientY };
});

document.addEventListener('keydown', (event) => {
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

        let nextHotspot = null;
        let closestDistance = Infinity;

        hotspots.forEach((hotspot) => {
            const toHotspot = hotspot.position.clone().sub(camera.position);
            const dotProduct = toHotspot.normalize().dot(direction);

            if (dotProduct > 0.5) {
                const distance = camera.position.distanceTo(hotspot.position);
                if (distance < closestDistance) {
                    closestDistance = distance;
                    nextHotspot = hotspot;
                }
            }
        });

        if (nextHotspot) {
            startPosition.copy(camera.position);
            startHotspot = findClosestHotspot();

            targetHotspot = nextHotspot;
            targetPosition.copy(nextHotspot.position);
        }
    }
});

let pitch = 0;
let yaw = 0;

const MAX_PITCH = Math.PI / 2;

const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
let intersectedFace = null;
let intersectionPoint = new THREE.Vector3();

document.addEventListener('mousemove', (event) => {
    mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
    mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

    if (isDragging) {
        const deltaX = event.clientX - previousMousePosition.x;
        const deltaY = event.clientY - previousMousePosition.y;

        yaw += deltaX * rotationSpeed;
        if (yaw > Math.PI) {
            yaw -= Math.PI * 2;
        } else if (yaw < -Math.PI) {
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
document.addEventListener('mouseup', () => {
    isDragging = false;
});

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

let currentHotspotIndex = 0; // Keep track of the current hotspot index

let disk = null;
const diskMaterial = new THREE.MeshBasicMaterial({
    color: 0xffff00,
    side: THREE.DoubleSide,
    transparent: true, // Important for renderOrder to work reliably
    opacity: 0.99, // Avoid full opacity which can cause issues
    depthWrite: false, // Prevents z-fighting with the object it sits on
    polygonOffset: true,
    polygonOffsetFactor: -1, // Adjust as needed
    polygonOffsetUnits: -1,
});

function updateRaycast() {
    // update the picking ray with the camera and mouse position
    raycaster.setFromCamera(mouse, camera);

    // calculate objects intersecting the picking ray
    const intersects = raycaster.intersectObjects(scene.children, true); // Check all children, including within loaded objects

    if (intersects.length > 0) {
        // Find the first intersected object that is a mesh
        let meshIntersection = null;
        for (let i = 0; i < intersects.length; i++) {
            if (intersects[i].object instanceof THREE.Mesh) {
                meshIntersection = intersects[i];
                break;
            }
        }

        if (meshIntersection) {
            if (!disk) {
                const diskGeometry = new THREE.CircleGeometry(0.1, 32);
                disk = new THREE.Mesh(diskGeometry, diskMaterial);
                scene.add(disk); // Add disk only once
            }
            
            intersectedFace = meshIntersection.face;
            intersectionPoint.copy(meshIntersection.point);
    
            // Calculate disk orientation (tangent to the face)
            const faceNormal = intersectedFace.normal.clone().transformDirection(meshIntersection.object.matrixWorld); // Important: Transform normal to world space
            const faceCenter = intersectionPoint;
    
            // Position and orient the disk
            disk.position.copy(faceCenter);
            disk.lookAt(faceCenter.clone().add(faceNormal));
    
        } else if (disk) {
            scene.remove(disk);
            disk = null;
        }
    } else {
        if (disk) {
            scene.remove(disk);
            disk = null;
        }
        intersectedFace = null;
        intersectionPoint.set(0,0,0);
    }
}

let previousTime = 0;
function render(time) {
    const deltaTime = (time - previousTime) / 1000;
    previousTime = time;

    camera.position.lerp(targetPosition, 0.1);

    if (startHotspot) {
        material.uniforms.panoramicTexture.value = startHotspot.panoramicTexture;
        material.uniforms.hotspotPosition.value.copy(startHotspot.position);
    }

    if (targetHotspot) {
        material.uniforms.targetPanoramicTexture.value = targetHotspot.panoramicTexture;
        material.uniforms.targetHotspotPosition.value.copy(targetHotspot.position);
    }

    const distanceToTarget = camera.position.distanceTo(targetHotspot.position);
    const totalDistance = startPosition.distanceTo(targetHotspot.position);

    var blendFactor = 1.0 - Math.max(0, Math.min(1, distanceToTarget / totalDistance));
    if (totalDistance < 0.01) {
        blendFactor = 1.0;
    }
    material.uniforms.blendFactor.value = blendFactor;
    
    updateRaycast();

    renderer.render(scene, camera);
    requestAnimationFrame(render);
}