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
let scoreIncrement;

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
let pipeInterval = 1200;
let lastTime = performance.now();
let pipeSpawnTimer = 0;
let jumpValue = -550;

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

const Difficulty = Object.freeze({ //freeze makes this immutable.
    EASY : "EASY",
    MEDIUM : "MEDIUM",
    HARD : "HARD",
});

let selectedDifficulty;
let paused = true;

function selectDifficulty(button) {
    const allButtons = document.querySelectorAll('.difficulty-button');
    for (let i = 0; i < allButtons.length; i++) {
        allButtons[i].disabled = true;
    }

    for(let i = 0; i < Object.values(Difficulty).length ; i++) {
        if (button.value === Difficulty.EASY) {
            selectedDifficulty = Difficulty.EASY;
            console.log("setting difficulty to easy")
            easyDifficultySettings();
        }
        if (button.value === Difficulty.MEDIUM) {
            selectedDifficulty = Difficulty.MEDIUM;
            console.log("setting difficulty to medium")
            mediumDifficultySettings();
        }
        if (button.value === Difficulty.HARD) {
            selectedDifficulty = Difficulty.HARD;
            console.log("setting difficulty to hard")
            hardDifficultySettings();
        }

    }

    startGame();
}

function easyDifficultySettings() {
    gravity = 1;
    pipeInterval = 2000;

    scoreIncrement = .5;


}
function mediumDifficultySettings() {
    gravity = 2.5;
    pipeInterval = 1750;

    scoreIncrement = 1;


}

function hardDifficultySettings() {
    gravity = 3;
    pipeInterval = 1500;
    velocityX = -2.5;
    scoreIncrement = 1;

}

//physics
let velocityX = -2; //use -2 for the game
let velocityY = 0; // bird jump speed
let gravity = 3; //pixels per millisecond squared



function startGame() {
    const startMessage = "Game starts in\n";
    const timeTillStart = 3000; // 6 seconds
    const startTime = performance.now();

    function countdownLoop(currentTime) {
        const elapsed = currentTime - startTime;
        const remaining = Math.ceil((timeTillStart - elapsed) / 1000);

        context.clearRect(0, 0, board.width, board.height); // Clear the canvas
        context.fillStyle = "white";
        context.font = "36px sans-serif";
        context.textAlign = "center";
        context.fillText(startMessage + remaining, board.width / 2, board.height / 2);

        if (elapsed < timeTillStart) {
            requestAnimationFrame(countdownLoop);
        } else {
            lastTime = performance.now();
            resetGame();
            requestAnimationFrame(gameLoop); // Start the game

        }
    }


    requestAnimationFrame(countdownLoop);


}

function gameLoop() {
    let now = performance.now();
    const deltaTime = (now - lastTime) / 1000; // delta in seconds
    lastTime = now;

    if (gameOver || paused) {
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
    console.log("Bird Y is " + bird.y.toString());

    drawBirdContext();


    if (bird.y > boardHeight) {
        sfxDie.play();
        gameOver = true;
        submitHighScore(score);
    }

    // pipes
    for (let i = 0; i < pipeArray.length; i++) {
        let pipe = pipeArray[i];
        pipe.x += velocityX * deltaTime * 60; // scale for consistent speed at 60fps

        context.drawImage(pipe.img, pipe.x, pipe.y, pipe.width, pipe.height);

        if (!pipe.passed && bird.x > pipe.x + pipe.width) {
            pipe.passed = true;
            sfxPoint.play();
            score += scoreIncrement;
        }

        if (detectCollision(bird, pipe)) {
            sfxHit.play();
            gameOver = true;
            submitHighScore(score);
        }
    }

    while (pipeArray.length > 0 && pipeArray[0].x < -pipeWidth) {
        pipeArray.shift();
    }


    context.fillStyle = "white";
    context.font = "45px sans-serif";
    context.fillText(score, board.width / 2, 40);
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

}


function resetGame() {
    if (selectedDifficulty !== null) {
        console.log("Resetting Game");
        bird.y = birdY;
        pipeArray = [];
        score = 0;
        gameOver = false;
        paused = false;
        lastTime = performance.now();
        requestAnimationFrame(gameLoop);
        if (!bgmLoaded) {
            bgmMario.play();
            bgmLoaded = true;
        }

    }


}

function moveBird(e) {

    if (e.code === "Space" || e.code === "ArrowUp" || e.code === "KeyX" || e.code === "mouseClick" ) {
        velocityY = jumpValue;

    }
    if (e.type === "click") { //this handles mouse clicks
        velocityY = jumpValue;

    }

    if (gameOver) {

        resetGame();
    }


}


function drawBirdContext() {

    context.drawImage(birdImg, bird.x, bird.y, bird.width, bird.height);

}


function placePipes() {

    if (gameOver || paused) {
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

function submitHighScore(score) {
    const timestamp = Date.now();
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    if (score === 0) {
        console.log("Score of 0, no submission.")
        return;
    }
    fetch('submit-score', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: JSON.stringify({score: score,
        }),


    })
    .then(res => res.json())
        .then(data => {
            console.log("server response", data);
        })
        .catch(err => console.error("error submitting score:", err));

}