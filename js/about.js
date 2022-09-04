const controls = new THREE.OrbitControls(g_Camera, g_Renderer.domElement);

g_Camera.position.set(0, 10, 0);
controls.update();


const geometry = new THREE.BoxGeometry(10, 1, 1);
const material = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
const cube = new THREE.Mesh(geometry, material);
g_Scene.add(cube);

g_Camera.position.z = 5;
g_Renderer.setClearColor(new THREE.Color());

function animate() {
    requestAnimationFrame(animate);

    // cube.rotation.x += 0.01;
    cube.rotation.y += 0.01;

    g_Renderer.render(g_Scene, g_Camera);
};

animate();

function onResize() {
    g_Renderer.setSize(window.innerWidth, window.innerHeight);

    g_Camera.aspect = window.innerWidth / window.innerHeight;
    g_Camera.updateProjectionMatrix();
}

window.addEventListener('resize', onResize);




/* WINDOW GRID: var $grid = $('.windows').masonry({
    itemSelector: '.window_container',
    columnWidth: 280,
    gutter: 10,
    horizontalOrder: true,
    fitWidth: true
});

$grid.imagesLoaded().progress(function () {
    $grid.masonry('layout');
}); */