// Imports
import * as THREE from 'three';
import { CSS3DRenderer, CSS3DObject } from 'three/addons/renderers/CSS3DRenderer.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import * as TWEEN from '@tweenjs/tween.js';

// Panel class
class Panel {
    constructor(element, position, scale, orientationTargetPos) {
        this.object = new CSS3DObject(element);
        this.orientationTargetPos = orientationTargetPos;
        this.object.position.set(position.x, position.y, position.z);
        this.object.scale.set(scale, scale, scale);
        this.object.lookAt(orientationTargetPos.x, orientationTargetPos.y, orientationTargetPos.z);
    }

    static fromTheta(element, theta, radius, scale) {
        const p = new Panel(element,
            new THREE.Vector3(0, radius * Math.sin(theta), radius * Math.cos(theta)),
            scale,
            new THREE.Vector3(0, radius * Math.sin(theta) * 1.1, radius * Math.cos(theta) * 1.1)
        )
        p.object.up.set(0, Math.sin(theta + Math.PI / 2), Math.cos(theta + Math.PI / 2));
        p.object.lookAt(0, radius * Math.sin(theta) * 1.1, radius * Math.cos(theta) * 1.1);
        p.theta = theta;
        p.radius = radius;
        return p;
    }

    setPositionFromTheta(theta, radius) {
        this.theta = theta;
        this.radius = radius;
        this.object.position.set(0, radius * Math.sin(theta), radius * Math.cos(theta));
        // this.object.up.set(0, Math.sin(theta + Math.PI/2), Math.cos(theta + Math.PI/2));
        // this.object.lookAt(this.orientationTargetPos.x, this.orientationTargetPos.y, this.orientationTargetPos.z);
    }
}

// PanelRing class
class PanelRing {
    constructor(radius, elements, gapTheta, avel, rot = new THREE.Vector3(0, 0, 0), pos = new THREE.Vector3(0, 0, 0)) {
        this.radius = radius;
        this.gapTheta = gapTheta;
        this.theta = 0;
        this.avel = avel;
        this.panels = [];
        this.TJSGroup = new THREE.Group();

        for (var idx = 0; idx < elements.length; idx++) {
            const panel = Panel.fromTheta(elements[idx], this.gapTheta * idx, this.radius, 0.01);
            this.enablePanelFollow(panel);
            this.panels.push(panel);
            this.TJSGroup.add(panel.object);
        }

        this.rot = rot;
        this.pos = pos;
        this.TJSGroup.position.set(pos.x, pos.y, pos.z);
    }

    enablePanelFollow(panel) {
        const ring = this;
        panel.object.element.onpointerdown = function (event) {
            // if following ring dont run following: 
            if (this === activeRing)
                return;
            // console.log(camera.position);

            activeRing = this;

            followActive = false;
            followRing.avel = ring.avel;
            followRing.rot = ring.rot;
            followRing.pos = ring.pos;
            followRing.panels[0].setPositionFromTheta(panel.theta, ring.radius + panelCameraOffset);
            followRing.panels[1].setPositionFromTheta(panel.theta + Math.PI / 2, 1);
            followRing.updateOrbit(globalTime + panelFollowAnimationDuration);

            const targetCameraPos = new THREE.Vector3();
            const targetUpVector = new THREE.Vector3();
            followRing.panels[0].object.getWorldPosition(targetCameraPos);
            followRing.panels[1].object.getWorldPosition(targetUpVector);


            const params = { cx: camera.position.x, cy: camera.position.y, cz: camera.position.z, ux: camera.up.x, uy: camera.up.y, uz: camera.up.z, tx: cameraTarget.x, ty: cameraTarget.y, tz: cameraTarget.z };
            const cameraAnimationTween = new TWEEN.Tween(params)
                .to({ cx: targetCameraPos.x, cy: targetCameraPos.y, cz: targetCameraPos.z, ux: targetUpVector.x - followRing.TJSGroup.position.x, uy: targetUpVector.y - followRing.TJSGroup.position.y, uz: targetUpVector.z - followRing.TJSGroup.position.z, tx: ring.pos.x, ty: ring.pos.y, tz: ring.pos.z }, panelFollowAnimationDuration)
                .onUpdate(() => {
                    camera.position.set(params.cx, params.cy, params.cz);
                    camera.up.set(params.ux, params.uy, params.uz);
                    camera.lookAt(params.tx, params.ty, params.tz);
                }
                ).onComplete(() => { startFollow(panel, ring.pos) })
                .start();
            globalTweenGroup.add(cameraAnimationTween);
        }
    }

    updateRingRotation(theta) {
        this.theta = theta;
        for (var idx = 0; idx < this.panels.length; idx++)
            this.panels[idx].setPositionFromTheta(this.gapTheta * idx + theta, this.radius);
    }

    updateOrbit(time) {
        this.TJSGroup.position.set(this.pos.x, this.pos.y, this.pos.z);
        this.TJSGroup.rotation.set(this.avel.x * time + this.rot.x, this.avel.y * time + this.rot.y, this.avel.z * time + this.rot.z);
    }
}

// Parameters
var panelFollowAnimationDuration = 1500;
var panelCameraOffset = 3.2;

// Globals
var db;
var rings = [];
var globalTime = 0;
var followActive = false;
var followObjectTheta = 0;
var activeRing = null;
var followRing = new PanelRing(1, [document.createElement('div'), document.createElement('div')], Math.PI / 2, new THREE.Vector3(0, 0, 0));
var cameraTarget = new THREE.Vector3(0, 0, 0);
const globalTweenGroup = new TWEEN.Group();

// Create scene, camera, renderers, and orbit controls
const scene = new THREE.Scene({ alpha: true, antialias: true });
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const CSSrenderer = new CSS3DRenderer();
const controls = new OrbitControls(camera, CSSrenderer.domElement);
const parent = document.getElementById("CSSRender");

camera.position.z = 70;
CSSrenderer.setSize(parent.offsetWidth, parent.offsetHeight);
parent.appendChild(CSSrenderer.domElement);
CSSrenderer.domElement.style.zIndex = 2;
CSSrenderer.domElement.style.position = 'relative';

// Start follow function
function startFollow(panel, ringPos) {
    cameraTarget = ringPos;
    followActive = true;
    followObjectTheta = panel.theta;
    controls.enableZoom = false;
    controls.target.set(ringPos.x, ringPos.y, ringPos.z);
}

// Camera follow function
function cameraFollow() {
    followRing.updateOrbit(globalTime);
    followRing.panels[0].setPositionFromTheta(followObjectTheta, followRing.panels[0].radius);
    followRing.panels[1].setPositionFromTheta(followObjectTheta + Math.PI / 2, 1);

    const targetCameraPos = new THREE.Vector3();
    const targetUpVector = new THREE.Vector3();
    followRing.panels[0].object.getWorldPosition(targetCameraPos);
    followRing.panels[1].object.getWorldPosition(targetUpVector);

    camera.position.set(targetCameraPos.x, targetCameraPos.y, targetCameraPos.z);
    camera.up.set(targetUpVector.x - followRing.TJSGroup.position.x, targetUpVector.y - followRing.TJSGroup.position.y, targetUpVector.z - followRing.TJSGroup.position.z);
    camera.lookAt(followRing.pos.x, followRing.pos.y, followRing.pos.z);
}

// Renderer click detection for resuming orbit controls
CSSrenderer.domElement.onpointerdown = function (e) {
    if (document.elementFromPoint(e.clientX, e.clientY) === CSSrenderer.domElement) {
        activeRing = null;
        followActive = false;
        controls.enableZoom = true;
    }
}

// Update when resized [kinda not working yet]
parent.addEventListener('resize', onWindowResize, false);
function onWindowResize() {

    camera.aspect = parent.offsetWidth / parent.offsetHeight;
    camera.updateProjectionMatrix();

    renderer.setSize(parent.offsetWidth, parent.offsetHeight);

}

// Update camera position on scroll 
CSSrenderer.domElement.onwheel = function (e) {
    followObjectTheta += -e.deltaY / 1000.0;
};


// Panel makers
function imagePanel(entry) {
    const elem = document.createElement('div');
    elem.classList.add('image_panel');
    elem.innerHTML =
        `<div class="panelHeader">
        ${entry['title']} by ${entry['author']}
        <div style="padding: 1px" class="button-group">
            <div style="scale: 0.65" class="button">
                <div class="full-screen-1"></div>
                <div class="full-screen-2"></div>
            </div>
        </div>
    </div>
    </div>
    <div class="fileHeader">
        <div class="WhiteBar"></div>
        <div class="fileInfo" onmousedown="showInfoWindow('${entry['title']}', '${entry['author']}', ${entry['project_month']}, ${entry['project_year']}, '${entry['description']}')">Information</div>
        <div class="fileComments" onmousedown="showCommentWindow(${entry[
        'id']})">Comments</div>
    </div>
    <img src="download/${entry['filename']}">`;
    return elem;
}

function audioPanel(entry) {
    const elem = document.createElement('div');
    elem.classList.add('audio_panel');
    elem.innerHTML =
        `<div class="panelHeader">
        [Project Title] by [Author/s]
        <div style="padding: 1px" class="button-group">
            <div style="scale: 0.65" class="button">
                <div class="full-screen-1"></div>
                <div class="full-screen-2"></div>
            </div>
        </div>
    </div>
    <div class="fileHeader">
        <div class="WhiteBar"></div>
        <div class="fileInfo">Information</div>
        <div class="fileComments">Comments</div>
    </div>
    <div class="audioContainer">
        <audio id="audioElement" src="download/${entry['filename']}" preload="auto"></audio>
        <div class="audioControls">
            <input type="range" id="progressBar" class="progress-bar" value="0" step="1">
            <div class="volume-container">
                <input type="range" id="volumeControl" class="volume-control" value="100" step="1">
            </div>
        </div>
    </div>`;
    return elem;
}

// Audio Controls
function addAudioControlListeners() {
    const audioElement = document.getElementById('audioElement');
    const playPauseBtn = document.querySelector('.playPauseBtn');
    const progressBar = document.querySelector('.progressBar');
    const volumeControl = document.querySelector('.volumeControl');

    playPauseBtn.addEventListener('click', function () {
        if (audioElement.paused) {
            audioElement.play();
            playPauseBtn.textContent = 'Pause';
        } else {
            audioElement.pause();
            playPauseBtn.textContent = 'Play';
        }
    });

    audioElement.addEventListener('timeupdate', function () {
        const progress = (audioElement.currentTime / audioElement.duration) * 100;
        progressBar.value = progress;
    });

    progressBar.addEventListener('input', function () {
        const value = progressBar.value;
        audioElement.currentTime = (audioElement.duration * value) / 100;
    });

    volumeControl.addEventListener('input', function () {
        audioElement.volume = volumeControl.value / 100;
    });
}

document.addEventListener('DOMContentLoaded', addAudioControlListeners);

function videoPanel(entry) {
    const elem = document.createElement('div');
    elem.classList.add('video_panel');
    elem.innerHTML =
        `<div class="panelHeader">
    ${entry['title']} by ${entry['author']}
    <div style="padding: 1px" class="button-group">
        <div style="scale: 0.65" class="button">
            <div class="full-screen-1"></div>
            <div class="full-screen-2"></div>
        </div>
    </div>
</div>
</div>
<div class="fileHeader">
    <div class="WhiteBar"></div>
    <div class="fileInfo" onmousedown="showInfoWindow('${entry['title']}', '${entry['author']}', ${entry['project_month']}, ${entry['project_year']}, '${entry['description']}')">Information</div>
    <div class="fileComments" onmousedown="showCommentWindow(${entry[
        'id']})">Comments</div>
</div>
<video controls>
    <source src="download/${entry['filename']}" type="video/mp4>
</video>`;
return elem;
}

// Scene setup function
function setupScene() {
    const ring_params = {
        '2022': { 'radius': 40, 'avel': new THREE.Vector3(0.0001, 0.00003, 0), 'rot': new THREE.Vector3(0, 0, Math.PI / 2), 'pos': new THREE.Vector3(0, 0, 0) },
        '2023': { 'radius': 44, 'avel': new THREE.Vector3(-0.0001, 0.00003, 0), 'rot': new THREE.Vector3(0, 0, Math.PI / 2), 'pos': new THREE.Vector3(0, 0, 0) },
        '2024': { 'radius': 48, 'avel': new THREE.Vector3(-0.0002, -0.00005, 0), 'rot': new THREE.Vector3(0, 0, 0), 'pos': new THREE.Vector3(0, 0, 0) },
        // '2025':{'radius':52, 'avel':new THREE.Vector3(0, 0, 0), 'rot':new THREE.Vector3(0, 0, 0), 'pos':new THREE.Vector3(0, 0, 0)},
    }

    var divs = [];
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/dbjson");
    xhr.onload = function (event) {
        db = JSON.parse(event.target.response);

        for (const [year, params] of Object.entries(ring_params)) {
            var elems = [];
            for (let idx in db) {
                if (!db[idx]['approved'] || db[idx]['project_year'] !== Number(year))
                    continue;

                if (db[idx]['filename'].split('.')[1].toUpperCase() === 'JPG')
                    elems.push(imagePanel(db[idx]));

                if (db[idx]['filename'].split('.')[1].toUpperCase() === 'MP3')
                    elems.push(audioPanel(db[idx]));

                if (db[idx]['filename'].split('.')[1].toUpperCase() === 'MP4')
                    elems.push(videoPanel(db[idx]));
            }
            rings.push(new PanelRing(params['radius'], elems, 2 * Math.PI / elems.length, params['avel'], params['rot'], params['pos']));
        }

        for (var ring of rings)
            scene.add(ring.TJSGroup);
    };
    xhr.send();
}

// Setup animation loop
function animate(time) {
    CSSrenderer.render(scene, camera);
    controls.update();
    globalTweenGroup.update();
    globalTime = time;

    if (followActive) {
        cameraFollow();
    }

    for (var ring of rings)
        ring.updateOrbit(globalTime);

    requestAnimationFrame(animate);
}

// Run setup
setupScene();
// Start animation
requestAnimationFrame(animate);
