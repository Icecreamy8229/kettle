let board;
let boardWidth = 360;
let boardHeight = 640;
let context;

/*
* General notes
* Top left position is considered 0,0
* numbers increase from down to right.
*
*
* */


let gameOver = false;
let score = 0;

//bird attributes
let birdWidth = 34; //width/height ratio = 408/228 = 17/12
let birdHeight = 24;
let birdX = boardWidth/8;
let birdY = boardHeight/2; //image anchor position is top left

//audio files
const sfxDie = new Audio('/static/kettlebird/audio/sfx_die.wav');
const sfxHit = new Audio('/static/kettlebird/audio/sfx_hit.wav');
const sfxPoint = new Audio('/static/kettlebird/audio/sfx_point.wav');
const bgmMario = new Audio('/static/kettlebird/audio/bgm_mario.mp3');
bgmMario.loop = true;

let bgmLoaded = false;


//time delta logic
const pipeInterval = 1200;
let lastTime = performance.now();
let pipeSpawnTimer = 0;

//the birb
let bird = {
    x : birdX,
    y : birdY,
    width : birdWidth,
    height : birdHeight
}

//pipes
let pipeArray = [];
let pipeWidth = 64; //width/height ratio = 384/3072 = 1/8
let pipeHeight = 512;
let pipeX = boardWidth;
let pipeY = 0;

let topPipeImg;
let bottomPipeImg;


//physics
let velocityX = -2; //use -2 for the game
let velocityY = 0; // bird jump speed
let gravity = 3.5; //pixels per millisecond squared


function gameLoop(currentTime) {
    const deltaTime = (currentTime - lastTime) / 1000; // delta in seconds
    lastTime = currentTime;

    if (gameOver) {
        console.log("Game Over");
        return;
    }

    pipeSpawnTimer += deltaTime;

    if (pipeSpawnTimer >= pipeInterval / 1000) { // convert pipeInterval to seconds
        placePipes();
        pipeSpawnTimer = 0;
    }

    context.clearRect(0, 0, boardWidth, boardHeight);

    // Apply gravity and movement using deltaTime
    velocityY += gravity * deltaTime * 1000; // gravity is per ms, so convert to px/sec²
    bird.y = Math.max(bird.y + velocityY * deltaTime, 0);

    drawBirdContext();

    if (bird.y > boardHeight) {
        sfxDie.play();
        gameOver = true;
    }

    // pipes
    for (let i = 0; i < pipeArray.length; i++) {
        let pipe = pipeArray[i];
        pipe.x += velocityX * deltaTime * 60; // scale for consistent speed at 60fps

        context.drawImage(pipe.img, pipe.x, pipe.y, pipe.width, pipe.height);

        if (!pipe.passed && bird.x > pipe.x + pipe.width) {
            pipe.passed = true;
            sfxPoint.play();
            score += 0.5;
        }

        if (detectCollision(bird, pipe)) {
            sfxHit.play();
            gameOver = true;
        }
    }

    while (pipeArray.length > 0 && pipeArray[0].x < -pipeWidth) {
        pipeArray.shift();
    }

    context.fillStyle = "white";
    context.font = "45px sans-serif";
    context.fillText(score, 5, 45);

    requestAnimationFrame(gameLoop);
}


window.onload = function () {

    board = document.getElementById("board");
    board.height = boardHeight;
    board.width = boardWidth;
    context = board.getContext("2d"); // used for drawing on the board.

    birdImg = new Image();
    birdImg.src = "/static/kettlebird/images/flappybird.png";
    birdImg.onload = function () {


        drawBirdContext();


    }

    topPipeImg = new Image();
    topPipeImg.src = "/static/kettlebird/images/toppipe.png";

    bottomPipeImg = new Image();
    bottomPipeImg.src = "/static/kettlebird/images/bottompipe.png";


    document.addEventListener("keydown", moveBird);
    document.addEventListener("click", moveBird);

    requestAnimationFrame(gameLoop);

}


function resetGame() {
    bird.y = birdY;
    pipeArray = [];
    score = 0;
    gameOver = false;
}

function moveBird(e) {

    if (e.code === "Space" || e.code === "ArrowUp" || e.code === "KeyX" || e.code === "mouseClick" ) {
        velocityY = -500;

    }
    if (e.type === "click") { //this handles mouse clicks
        velocityY = -500;

    }

    if (gameOver) {

        resetGame();
    }

    if (!bgmLoaded) {
        bgmMario.play();
        bgmLoaded = true;
    }
}


function drawBirdContext() {

    context.drawImage(birdImg, bird.x, bird.y, bird.width, bird.height);

}


function placePipes() {

    if (gameOver) {
        return;
    }

    let randomPipeY = pipeY - pipeHeight / 4 - Math.random()*(pipeHeight / 2);
    let openingSpace = board.height/4;

    let topPipe = {
        img : topPipeImg,
        x : pipeX,
        y : randomPipeY,
        width : pipeWidth,
        height : pipeHeight,
        passed : false //checks if the bird has passed this pipe object
    }

    let bottomPipe = {
        img : bottomPipeImg,
        x : pipeX,
        y : randomPipeY + pipeHeight + openingSpace,
        width : pipeWidth,
        height : pipeHeight,
        passed : false
    }

    pipeArray.push(topPipe);
    pipeArray.push(bottomPipe);

}

function detectCollision(a, b) {
    return a.x < b.x + b.width &&
        a.x + a.width > b.x &&
        a.y < b.y + b.height &&
        a.y + a.height > b.y;
}