// GameQuest JavaScript
let currentGameResults = [];

// Load filter options on page load
document.addEventListener("DOMContentLoaded", function () {
  loadFilterOptions();
  setupImageUpload();
});

function setupImageUpload() {
  const fileInput = document.getElementById("imageFileInput");
  const uploadArea = document.getElementById("imageUploadArea");

  // Handle file input change
  fileInput.addEventListener("change", function (e) {
    const file = e.target.files[0];
    if (file) {
      showImagePreview(file);
    }
  });

  // Handle drag and drop
  uploadArea.addEventListener("dragover", function (e) {
    e.preventDefault();
    uploadArea.classList.add("dragover");
  });

  uploadArea.addEventListener("dragleave", function (e) {
    e.preventDefault();
    uploadArea.classList.remove("dragover");
  });

  uploadArea.addEventListener("drop", function (e) {
    e.preventDefault();
    uploadArea.classList.remove("dragover");

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file.type.startsWith("image/")) {
        fileInput.files = files;
        showImagePreview(file);
      } else {
        alert("Please select an image file");
      }
    }
  });

  // Handle click to select file
  uploadArea.addEventListener("click", function () {
    fileInput.click();
  });
}

function showImagePreview(file) {
  const reader = new FileReader();

  reader.onload = function (e) {
    document.getElementById("imagePreview").src = e.target.result;
    document.getElementById("imageUploadArea").style.display = "none";
    document.getElementById("imagePreviewContainer").style.display = "block";
  };

  reader.readAsDataURL(file);
}

// Load filter options from server
async function loadFilterOptions() {
  try {
    // Load platforms
    const platformsResponse = await fetch("/api/platforms");
    const platforms = await platformsResponse.json();

    const platformSelect = document.getElementById("platformFilter");
    platforms.forEach((platform) => {
      const option = document.createElement("option");
      option.value = platform;
      option.textContent = platform;
      platformSelect.appendChild(option);
    });

    // Load genres
    const genresResponse = await fetch("/api/genres");
    const genres = await genresResponse.json();

    const genreSelect = document.getElementById("genreFilter");
    genres.forEach((genre) => {
      const option = document.createElement("option");
      option.value = genre;
      option.textContent = genre;
      genreSelect.appendChild(option);
    });
  } catch (error) {
    console.error("Error loading filter options:", error);
  }
}

// Search functions
async function searchGames() {
  const query = document.getElementById("searchInput").value.trim();
  if (!query) {
    alert("Please enter a search query");
    return;
  }

  const filters = getFilters();
  showLoading("Searching games...");

  try {
    const response = await fetch(
      `/api/search?q=${encodeURIComponent(query)}&${buildQueryString(filters)}`
    );
    const data = await response.json();

    if (data.error) {
      showError(data.error);
    } else {
      displayGames(data.games, "Text Search Results");
    }
  } catch (error) {
    console.error("Error:", error);
    showError("Search failed: " + error.message);
  }
}

async function semanticSearchGames() {
  const query = document.getElementById("searchInput").value.trim();
  if (!query) {
    alert("Please enter a search query");
    return;
  }

  const filters = getFilters();
  showLoading("Performing semantic search...");

  try {
    const response = await fetch(
      `/api/semantic-search?q=${encodeURIComponent(query)}&${buildQueryString(
        filters
      )}`
    );
    const data = await response.json();

    if (data.error) {
      showError(data.error);
    } else {
      displayGames(data.games, "Vector Search Results");
    }
  } catch (error) {
    console.error("Error:", error);
    showError("Semantic search failed: " + error.message);
  }
}

// Global variable to store current search type
let currentSearchType = "covers";

function openImageUploadModal(searchType) {
  currentSearchType = searchType;
  const title =
    searchType === "covers" ? "Cover Image Search" : "Screenshot Search";
  document.getElementById("imageUploadTitle").textContent = title;
  document.getElementById("imageUploadModal").classList.add("show");
}

function closeImageUploadModal() {
  document.getElementById("imageUploadModal").classList.remove("show");
  resetImageUpload();
}

function resetImageUpload() {
  document.getElementById("imageFileInput").value = "";
  document.getElementById("imageUploadArea").style.display = "block";
  document.getElementById("imagePreviewContainer").style.display = "none";
}

async function searchByUploadedImage() {
  const fileInput = document.getElementById("imageFileInput");
  const file = fileInput.files[0];

  if (!file) {
    alert("Please select an image file first");
    return;
  }

  // Validate file type
  if (!file.type.startsWith("image/")) {
    alert("Please select a valid image file");
    return;
  }

  const filters = getFilters();
  const searchTypeText =
    currentSearchType === "covers" ? "Cover" : "Screenshot";
  showLoading(`Finding games with similar ${searchTypeText.toLowerCase()}...`);

  // Close modal
  closeImageUploadModal();

  try {
    const formData = new FormData();
    formData.append("image", file);
    formData.append("search_type", currentSearchType);

    // Add filters to form data
    Object.entries(filters).forEach(([key, value]) => {
      if (value || key === "scored_only") {
        formData.append(key, value);
      }
    });

    const response = await fetch("/api/upload-image-search", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (data.error) {
      showError(data.error);
    } else {
      const title = `Similar ${searchTypeText} Results`;
      displayGames(data.games, title);
    }
  } catch (error) {
    console.error("Error:", error);
    showError("Image search failed: " + error.message);
  }
}

async function agenticRAGSearch() {
  const query = document.getElementById("searchInput").value.trim();
  if (!query) {
    alert("Please enter a search query");
    return;
  }

  const filters = getFilters();
  showLoading("Agent is thinking...");

  try {
    const response = await fetch(
      `/api/agentic-rag?q=${encodeURIComponent(query)}&${buildQueryString(
        filters
      )}`
    );
    const data = await response.json();

    if (data.error) {
      showError(data.error);
    } else {
      displayAgenticResults(data);
    }
  } catch (error) {
    console.error("Error:", error);
    showError("Agentic RAG failed: " + error.message);
  }
}

// Helper functions
function getFilters() {
  return {
    platform: document.getElementById("platformFilter").value,
    genre: document.getElementById("genreFilter").value,
    score: document.getElementById("scoreFilter").value,
    year: document.getElementById("yearFilter").value,
    scored_only: document.getElementById("scoredOnlyFilter").checked,
  };
}

function buildQueryString(filters) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value || key === "scored_only") {
      params.append(key, value);
    }
  });
  return params.toString();
}

// Display functions
function displayAgenticResults(data) {
  const resultsSection = document.getElementById("resultsSection");

  let html = "<h2>AI Agent Recommendations</h2>";

  // Display structured game data
  if (data.games && data.games.length > 0) {
    currentGameResults = data.games; // Store for modal access
    data.games.forEach((game) => {
      html += createGameCard(game);
    });
  }

  resultsSection.innerHTML = html;

  // Create AI sidebar if response exists
  if (data.response) {
    createAISidebar(data.response);
  } else {
    removeAISidebar();
  }
}

function displayGames(games, title) {
  const resultsSection = document.getElementById("resultsSection");

  let html = `<h2>${title}</h2>`;

  if (games && games.length > 0) {
    currentGameResults = games; // Store for modal access
    games.forEach((game) => {
      html += createGameCard(game);
    });
  } else {
    html += "<p>No games found matching your criteria.</p>";
  }

  resultsSection.innerHTML = html;

  // Remove AI sidebar for non-agentic searches
  removeAISidebar();
}

function createGameCard(game) {
  let year = "Unknown";
  if (game.release_date) {
    if (typeof game.release_date === "string") {
      // Handle various date formats
      if (game.release_date.includes("-")) {
        year = game.release_date.split("-")[0];
      } else if (game.release_date.includes("/")) {
        year =
          game.release_date.split("/")[2] || game.release_date.split("/")[0];
      } else {
        year = game.release_date.substring(0, 4);
      }
    } else {
      // Handle Date objects
      const date = new Date(game.release_date);
      year = date.getFullYear();
    }
  }

  const platforms = game.platforms ? game.platforms.join(", ") : "Unknown";
  const genres = game.genres ? game.genres.join(", ") : "Unknown";
  const coverUrl = game.id ? `/cover/${game.id}` : "";

  // Only show score if it exists and is not N/A
  let scoreHtml = "";
  if (
    game.moby_score !== null &&
    game.moby_score !== undefined &&
    game.moby_score !== "N/A"
  ) {
    let scoreClass = "";
    if (typeof game.moby_score === "number") {
      if (game.moby_score >= 8) scoreClass = "score-high";
      else if (game.moby_score >= 6) scoreClass = "score-medium";
      else scoreClass = "score-low";
    }
    scoreHtml = `<span class="meta-item ${scoreClass}">Score: ${game.moby_score}/10</span>`;
  }

  // Truncate description for main view
  let shortDescription = "";
  if (game.description) {
    shortDescription =
      game.description.length > 150
        ? game.description.substring(0, 150) + "..."
        : game.description;
  }

  let html = `
        <div class="game-card" onclick="showGameDetails(${game.id})">
            <div class="game-header">
                <img src="${coverUrl}" alt="${game.title}" class="game-cover" 
                     onerror="this.style.display='none'">
                <div class="game-info">
                    <h3 class="game-title">${game.title}</h3>
                    <div class="game-meta">
                        <span class="meta-item">${year}</span>
                        ${scoreHtml}
                        <span class="meta-item">${platforms}</span>
                    </div>
                    <p class="meta-item">${genres}</p>
                    ${
                      shortDescription
                        ? `<div class="game-description-short">${shortDescription}</div>`
                        : ""
                    }
                </div>
            </div>
            <div class="click-hint">Click for details</div>
        </div>
    `;

  return html;
}

function showLoading(message) {
  document.getElementById("resultsSection").innerHTML = `
        <div class="loading">
            <p>${message}</p>
        </div>
    `;
}

function showError(message) {
  document.getElementById("resultsSection").innerHTML = `
        <div class="error">
            <strong>Error:</strong> ${message}
        </div>
    `;
}

// Game detail modal functions
function showGameDetails(gameId) {
  // Find the game data from the current results
  const gameData = findGameById(gameId);
  if (!gameData) {
    console.error("Game data not found for ID:", gameId);
    return;
  }

  // Populate modal content
  document.getElementById("modalTitle").textContent = gameData.title;

  let year = "Unknown";
  if (gameData.release_date) {
    if (typeof gameData.release_date === "string") {
      if (gameData.release_date.includes("-")) {
        year = gameData.release_date.split("-")[0];
      } else if (gameData.release_date.includes("/")) {
        year =
          gameData.release_date.split("/")[2] ||
          gameData.release_date.split("/")[0];
      } else {
        year = gameData.release_date.substring(0, 4);
      }
    } else {
      const date = new Date(gameData.release_date);
      year = date.getFullYear();
    }
  }

  const platforms = gameData.platforms
    ? gameData.platforms.join(", ")
    : "Unknown";
  const genres = gameData.genres ? gameData.genres.join(", ") : "Unknown";
  const coverUrl = gameData.id ? `/cover/${gameData.id}` : "";

  // Score display
  let scoreHtml = "";
  if (
    gameData.moby_score !== null &&
    gameData.moby_score !== undefined &&
    gameData.moby_score !== "N/A"
  ) {
    let scoreClass = "";
    if (typeof gameData.moby_score === "number") {
      if (gameData.moby_score >= 8) scoreClass = "score-high";
      else if (gameData.moby_score >= 6) scoreClass = "score-medium";
      else scoreClass = "score-low";
    }
    scoreHtml = `<span class="meta-item ${scoreClass}">Score: ${gameData.moby_score}/10</span>`;
  }

  // Screenshots
  let screenshotsHtml = "";
  if (gameData.screenshot_paths && gameData.screenshot_paths.length > 0) {
    screenshotsHtml = `
            <div class="modal-screenshots">
                <h4>Screenshots</h4>
                <div class="screenshot-container">
                    ${gameData.screenshot_paths
                      .slice(0, 10)
                      .map(
                        (url) => `
                        <div class="screenshot-item">
                            <img src="${url}" alt="Screenshot" onerror="this.style.display='none'">
                        </div>
                    `
                      )
                      .join("")}
                </div>
            </div>
        `;
  }

  // Critics
  let criticsHtml = "";
  if (gameData.critics && gameData.critics.length > 0) {
    criticsHtml = `
            <div class="modal-critics">
                <h4>Critic Reviews</h4>
                ${gameData.critics
                  .map((critic) => {
                    const reviewText = critic.review || "";

                    return `
                    <div class="critic-card">
                        <div class="critic-content">${reviewText}</div>
                    </div>
                `;
                  })
                  .join("")}
            </div>
        `;
  }

  const modalContent = `
        <img src="${coverUrl}" alt="${gameData.title}" class="modal-game-cover" 
             onerror="this.style.display='none'">
        <div class="modal-game-info">
            <h2 class="modal-game-title">${gameData.title}</h2>
            <div class="modal-game-meta">
                <span class="meta-item">${year}</span>
                ${scoreHtml}
                <span class="meta-item">${platforms}</span>
                <span class="meta-item">${genres}</span>
            </div>
        </div>
        ${
          gameData.description
            ? `
            <div class="modal-description">
                <h4>Description</h4>
                <p>${gameData.description}</p>
            </div>
        `
            : ""
        }
        ${screenshotsHtml}
        ${criticsHtml}
    `;

  document.getElementById("modalBody").innerHTML = modalContent;
  document.getElementById("gameModal").classList.add("show");
}

function closeGameDetails() {
  document.getElementById("gameModal").classList.remove("show");
}

function findGameById(gameId) {
  // Find the game in the currently displayed results
  const game = currentGameResults.find((g) => g.id === gameId);
  if (game) {
    return game;
  }

  console.warn("Game data not found for ID:", gameId);
  return null;
}

// Close modal when clicking outside
document.getElementById("gameModal").addEventListener("click", function (e) {
  if (e.target === this) {
    closeGameDetails();
  }
});

// Close image upload modal when clicking outside
document
  .getElementById("imageUploadModal")
  .addEventListener("click", function (e) {
    if (e.target === this) {
      closeImageUploadModal();
    }
  });

// AI Sidebar functions
function createAISidebar(response) {
  // Remove existing sidebar if any
  removeAISidebar();

  // Clean up the response text
  const cleanResponse = cleanAIResponse(response);

  // Create sidebar HTML
  const sidebarHTML = `
        <div class="ai-sidebar open" id="aiSidebar">
            <div class="ai-sidebar-header">
                <h3 class="ai-sidebar-title">🤖 AI Analysis</h3>
                <button class="ai-sidebar-toggle" onclick="toggleAISidebar()">×</button>
            </div>
            <div class="ai-sidebar-content">
                ${cleanResponse}
            </div>
        </div>
        <button class="ai-sidebar-trigger" onclick="toggleAISidebar()" id="aiSidebarTrigger">
            🤖
        </button>
    `;

  // Add to body
  document.body.insertAdjacentHTML("beforeend", sidebarHTML);
}

function removeAISidebar() {
  const existingSidebar = document.getElementById("aiSidebar");
  const existingTrigger = document.getElementById("aiSidebarTrigger");

  if (existingSidebar) {
    existingSidebar.remove();
  }
  if (existingTrigger) {
    existingTrigger.remove();
  }
}

function toggleAISidebar() {
  const sidebar = document.getElementById("aiSidebar");
  if (sidebar) {
    sidebar.classList.toggle("open");
  }
}

function cleanAIResponse(response) {
  // Remove any filter text that might appear at the end
  let cleanText = response.replace(
    /I applied filters:.*?\. These are ranked by relevance\.?$/g,
    ""
  );

  // Simple approach: Find where analysis starts, everything before is thinking
  const analysisStartPatterns = [
    /Based on your query/i,
    /Here are the games/i,
    /I found \d+ games/i,
    /^\d+\. \*\*.*?\*\* \(/m,
    /Recommendations:/i,
  ];

  // Find the earliest analysis start pattern
  let analysisStartIndex = -1;
  for (const pattern of analysisStartPatterns) {
    const match = cleanText.search(pattern);
    if (
      match !== -1 &&
      (analysisStartIndex === -1 || match < analysisStartIndex)
    ) {
      analysisStartIndex = match;
    }
  }

  // If we found an analysis start and there's substantial content before it
  if (analysisStartIndex !== -1) {
    const thinkingPart = cleanText.substring(0, analysisStartIndex).trim();
    const analysisPart = cleanText.substring(analysisStartIndex).trim();

    // Only split if there's meaningful thinking content (more than just a few words)
    if (thinkingPart.length > 50) {
      // Format thinking section in light gray
      const thinkingHTML = `<div class="thinking-section">${thinkingPart.replace(
        /\n/g,
        "<br>"
      )}</div>`;

      // Format analysis section normally
      const analysisHTML = formatAnalysisSection(analysisPart);

      return `<div class="ai-response-content">${thinkingHTML}${analysisHTML}</div>`;
    }
  }

  // If no clear thinking/analysis split detected, format normally
  return `<div class="ai-response-content">${formatAnalysisSection(
    cleanText
  )}</div>`;
}

function formatAnalysisSection(text) {
  const sections = text.split("\n\n").filter((section) => section.trim());
  let formattedHTML = "";

  for (let i = 0; i < sections.length; i++) {
    const section = sections[i].trim();

    if (section.startsWith("Based on your query")) {
      // Intro text
      formattedHTML += `<div class="ai-intro">${section.replace(
        /\n/g,
        "<br>"
      )}</div>`;
    } else if (section.match(/^\d+\. \*\*.*?\*\* \(.*?\)/)) {
      // Game recommendation - format as card
      const gameMatch = section.match(
        /^(\d+)\. \*\*(.*?)\*\* \(([^)]+)\)\s*(.*)/
      );
      if (gameMatch) {
        const [, number, title, year, rest] = gameMatch;
        const reasonMatch = rest.match(/🎯 \*\*Why I recommend it\*\*: (.*)/);
        const reason = reasonMatch ? reasonMatch[1] : rest;

        formattedHTML += `
          <div class="game-item">
            <h4>${title} (${year})</h4>
            <div class="game-details">
              <strong>🎯 Why I recommend it:</strong> ${reason}
            </div>
          </div>
        `;
      }
    } else if (section.trim()) {
      // Other content
      formattedHTML += `<div class="ai-intro">${section.replace(
        /\n/g,
        "<br>"
      )}</div>`;
    }
  }

  return formattedHTML;
}
