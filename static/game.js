let pokeball = document.getElementById("pokeball");
let pokemonImages = document.querySelectorAll(".pokemon-game-image");
let gameStarted = false;
let interval;

// Function to get a random position inside the grid
function getRandomPosition() {
  let randomIndex = Math.floor(Math.random() * pokemonImages.length);
  let targetPokemon = pokemonImages[randomIndex];
  let rect = targetPokemon.getBoundingClientRect();
  let gameAreaRect = document.getElementById("game-area").getBoundingClientRect();

  // Calculate the position for the pokeball
  let left = rect.left - gameAreaRect.left + (rect.width / 2) - (pokeball.width / 2);
  let top = rect.top - gameAreaRect.top + (rect.height / 2) - (pokeball.height / 2);

  return { left, top };
}

// Function to move the Pokéball to a random position
function movePokeball() {
  if (!gameStarted) return;

  let position = getRandomPosition();
  pokeball.style.left = position.left + "px";
  pokeball.style.top = position.top + "px";
}

// Function to start the game
function startGame() {
  if (gameStarted) return;  // Prevent starting the game multiple times
  gameStarted = true;

  interval = setInterval(movePokeball, 100);  // Start moving the Pokéball every 100ms

  // Disable the start button after starting the game
  document.getElementById("start-button").disabled = true;

  // Stop the game after 5 seconds (for example)
  setTimeout(stopGame, 5000);
}

// Function to stop the game and "catch" a Pokémon
function stopGame() {
  gameStarted = false;

  // Make the Pokéball stop at a random position
  let position = getRandomPosition();
  pokeball.style.left = position.left + "px";
  pokeball.style.top = position.top + "px";

  // Enlarge the "caught" Pokémon
//   let caughtPokemon = document.elementFromPoint(position.left, position.top);
//   caughtPokemon.style.transform = "scale(1.5)";  // Make the caught Pokémon larger
//   caughtPokemon.style.transition = "transform 0.3s ease";

  // Re-enable the button to allow for another game
  document.getElementById("start-button").disabled = false;

  // Stop the Pokéball animation
  clearInterval(interval);
}
