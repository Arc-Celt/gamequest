/**
 * GameQuest Frontend JavaScript
 * Handles all frontend interactions and API calls
 */

class GameQuestApp {
  constructor() {
    this.apiBase = "/api";
    this.currentResults = [];
    this.filterOptions = null;
    this.init();
  }

  init() {
    this.setupEventListeners();
    this.loadFilterOptions();
    this.setupRangeSliders();
    this.checkHealth();
  }

  setupEventListeners() {
    // Main search input
    const mainSearchInput = document.getElementById("mainSearchInput");
    if (mainSearchInput) {
      mainSearchInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
          this.performMainSearch();
        }
      });
    }

    // Image upload
    const imageUpload = document.getElementById("imageUpload");
    if (imageUpload) {
      imageUpload.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
          this.performImageSearch(e.target.files[0]);
        }
      });
    }

    // Range sliders
    this.setupRangeSliders();
  }

  setupRangeSliders() {
    // Min Score slider
    const minScoreSlider = document.getElementById("minScore");
    const minScoreValue = document.getElementById("minScoreValue");
    if (minScoreSlider && minScoreValue) {
      minScoreSlider.addEventListener("input", (e) => {
        minScoreValue.textContent = parseFloat(e.target.value).toFixed(1);
      });
    }

    // Min Year slider
    const minYearSlider = document.getElementById("minYear");
    const minYearValue = document.getElementById("minYearValue");
    if (minYearSlider && minYearValue) {
      minYearSlider.addEventListener("input", (e) => {
        minYearValue.textContent = e.target.value;
      });
    }
  }

  async checkHealth() {
    try {
      const response = await fetch(`${this.apiBase}/health`);
      const data = await response.json();

      if (data.status === "healthy") {
        console.log("✅ API is healthy");
        this.showNotification("API is ready!", "success");
      } else {
        console.warn("⚠️ API health check failed");
        this.showNotification("API is not ready", "warning");
      }
    } catch (error) {
      console.error("❌ Health check failed:", error);
      this.showNotification("Cannot connect to API", "danger");
    }
  }

  async loadFilterOptions() {
    try {
      const response = await fetch(`${this.apiBase}/filter-options`);
      const data = await response.json();

      this.filterOptions = data;
      this.populateFilterOptions(data);
    } catch (error) {
      console.error("Failed to load filter options:", error);
      this.showNotification("Failed to load filter options", "danger");
    }
  }

  populateFilterOptions(options) {
    // Populate genres
    const genreFilter = document.getElementById("genreFilter");
    if (genreFilter && options.genres) {
      genreFilter.innerHTML = "";
      options.genres.forEach((genre) => {
        const option = document.createElement("option");
        option.value = genre;
        option.textContent = genre;
        genreFilter.appendChild(option);
      });
    }

    // Populate platforms
    const platformFilter = document.getElementById("platformFilter");
    if (platformFilter && options.platforms) {
      platformFilter.innerHTML = "";
      options.platforms.forEach((platform) => {
        const option = document.createElement("option");
        option.value = platform;
        option.textContent = platform;
        platformFilter.appendChild(option);
      });
    }

    // Update range sliders
    const minScoreSlider = document.getElementById("minScore");
    const minYearSlider = document.getElementById("minYear");

    if (minScoreSlider && options.score_range) {
      minScoreSlider.min = options.score_range.min;
      minScoreSlider.max = options.score_range.max;
      minScoreSlider.value = options.score_range.min;
      document.getElementById("minScoreValue").textContent =
        options.score_range.min.toFixed(1);
    }

    if (minYearSlider && options.year_range) {
      minYearSlider.min = options.year_range.min;
      minYearSlider.max = options.year_range.max;
      minYearSlider.value = options.year_range.min;
      document.getElementById("minYearValue").textContent =
        options.year_range.min;
    }
  }

  async performMainSearch() {
    const input = document.getElementById("mainSearchInput");
    if (!input || !input.value.trim()) {
      this.showNotification("Please enter a search query", "warning");
      return;
    }

    await this.performSearch(input.value.trim());
    input.value = "";
  }

  async performSearch(query) {
    this.showLoading(true);

    try {
      const numResults = document.getElementById("numResults")?.value || 10;

      const response = await fetch(`${this.apiBase}/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query,
          num_results: parseInt(numResults),
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      this.displaySearchResults(data.results, `Search results for "${query}"`);
    } catch (error) {
      console.error("Search failed:", error);
      this.showNotification("Search failed. Please try again.", "danger");
    } finally {
      this.showLoading(false);
    }
  }

  async performImageSearch(file) {
    this.showLoading(true);

    try {
      const formData = new FormData();
      formData.append("image", file);
      formData.append(
        "num_results",
        document.getElementById("numResults")?.value || 10
      );

      const response = await fetch(`${this.apiBase}/upload-image`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      this.displaySearchResults(
        data.results,
        `Games similar to uploaded image`
      );
    } catch (error) {
      console.error("Image search failed:", error);
      this.showNotification("Image search failed. Please try again.", "danger");
    } finally {
      this.showLoading(false);
    }
  }

  async applyFilters() {
    this.showLoading(true);

    try {
      const genres = Array.from(
        document.getElementById("genreFilter").selectedOptions
      )
        .map((option) => option.value)
        .filter((v) => v);

      const platforms = Array.from(
        document.getElementById("platformFilter").selectedOptions
      )
        .map((option) => option.value)
        .filter((v) => v);

      const minScore = parseFloat(document.getElementById("minScore").value);
      const minYear = parseInt(document.getElementById("minYear").value);

      const response = await fetch(`${this.apiBase}/filter`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          genres: genres.length > 0 ? genres : null,
          platforms: platforms.length > 0 ? platforms : null,
          min_score: minScore > 0 ? minScore : null,
          min_year: minYear > 1980 ? minYear : null,
          num_results: 20,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      this.displayFilterResults(data);
    } catch (error) {
      console.error("Filter failed:", error);
      this.showNotification("Filter failed. Please try again.", "danger");
    } finally {
      this.showLoading(false);
    }
  }

  clearFilters() {
    document.getElementById("genreFilter").selectedIndex = -1;
    document.getElementById("platformFilter").selectedIndex = -1;
    document.getElementById("minScore").value =
      document.getElementById("minScore").min;
    document.getElementById("minYear").value =
      document.getElementById("minYear").min;

    document.getElementById("minScoreValue").textContent = parseFloat(
      document.getElementById("minScore").value
    ).toFixed(1);
    document.getElementById("minYearValue").textContent =
      document.getElementById("minYear").value;
  }

  displaySearchResults(results, title) {
    const container = document.getElementById("searchResults");
    if (!container) return;

    if (results.length === 0) {
      container.innerHTML = `
                <div class="text-center text-muted py-5">
                    <i class="fas fa-search fa-3x mb-3"></i>
                    <h4>No games found</h4>
                    <p>Try different search terms or adjust your criteria</p>
                </div>
            `;
      return;
    }

    const resultsHtml = `
            <div class="mb-4">
                <h4>${title}</h4>
                <p class="text-muted">Found ${results.length} games</p>
            </div>
            <div class="row">
                ${results.map((game) => this.createGameCard(game)).join("")}
            </div>
        `;

    container.innerHTML = resultsHtml;
    container.scrollIntoView({ behavior: "smooth" });
  }

  displayFilterResults(data) {
    const container = document.getElementById("filterResults");
    if (!container) return;

    const { games, total_count } = data;

    if (games.length === 0) {
      container.innerHTML = `
                <div class="text-center text-muted py-5">
                    <i class="fas fa-filter fa-3x mb-3"></i>
                    <h4>No games found</h4>
                    <p>Try adjusting your filter criteria</p>
                </div>
            `;
      return;
    }

    const resultsHtml = `
            <div class="mb-4">
                <h4>Filtered Games</h4>
                <p class="text-muted">Showing ${
                  games.length
                } of ${total_count} games</p>
            </div>
            <div class="row">
                ${games.map((game) => this.createGameCard(game)).join("")}
            </div>
        `;

    container.innerHTML = resultsHtml;
    container.scrollIntoView({ behavior: "smooth" });
  }

  createGameCard(game) {
    const coverUrl = game.cover_path
      ? `/static/images/covers/${game.id}/cover.jpg`
      : "https://via.placeholder.com/300x200?text=No+Cover";

    const platforms = Array.isArray(game.platforms)
      ? game.platforms.slice(0, 3)
      : [];
    const genres = Array.isArray(game.genres) ? game.genres.slice(0, 3) : [];

    const score =
      game.relevance_score || game.similarity_score || game.moby_score;
    const scoreText = score
      ? typeof score === "number"
        ? score.toFixed(2)
        : score
      : "N/A";

    return `
            <div class="col-md-6 col-lg-4">
                <div class="game-card" onclick="gameApp.showGameDetails(${
                  game.game_id || game.id
                })">
                    <div class="position-relative">
                        <img src="${coverUrl}" class="card-img-top" alt="${
      game.title
    }" 
                             onerror="this.src='https://via.placeholder.com/300x200?text=No+Cover'">
                        <div class="game-score">${scoreText}</div>
                    </div>
                    <div class="card-body">
                        <h6 class="card-title">${game.title}</h6>
                        <p class="card-text text-truncate-2">${
                          game.description || "No description available"
                        }</p>
                        
                        ${
                          platforms.length > 0
                            ? `
                            <div class="mb-2">
                                ${platforms
                                  .map(
                                    (platform) =>
                                      `<span class="badge bg-primary">${platform}</span>`
                                  )
                                  .join(" ")}
                            </div>
                        `
                            : ""
                        }
                        
                        ${
                          genres.length > 0
                            ? `
                            <div class="mb-2">
                                ${genres
                                  .map(
                                    (genre) =>
                                      `<span class="badge bg-secondary">${genre}</span>`
                                  )
                                  .join(" ")}
                            </div>
                        `
                            : ""
                        }
                        
                        ${
                          game.release_date
                            ? `
                            <small class="text-muted">
                                <i class="fas fa-calendar me-1"></i>${new Date(
                                  game.release_date
                                ).getFullYear()}
                            </small>
                        `
                            : ""
                        }
                    </div>
                </div>
            </div>
        `;
  }

  async showGameDetails(gameId) {
    try {
      const response = await fetch(`${this.apiBase}/game/${gameId}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const game = await response.json();
      this.displayGameModal(game);
    } catch (error) {
      console.error("Failed to load game details:", error);
      this.showNotification("Failed to load game details", "danger");
    }
  }

  displayGameModal(game) {
    const modal = new bootstrap.Modal(
      document.getElementById("gameDetailModal")
    );
    const title = document.getElementById("gameDetailTitle");
    const body = document.getElementById("gameDetailBody");
    const link = document.getElementById("gameDetailLink");

    title.textContent = game.title;
    link.href = game.moby_url || "#";

    const coverUrl = game.cover_path
      ? `/static/images/covers/${game.id}/cover.jpg`
      : "https://via.placeholder.com/400x300?text=No+Cover";

    const criticsHtml =
      game.critics && game.critics.length > 0
        ? `
            <div class="mt-4">
                <h6><i class="fas fa-quote-left me-2"></i>Critic Reviews</h6>
                ${game.critics
                  .slice(0, 3)
                  .map(
                    (critic) => `
                    <div class="critic-quote">
                        "${critic}"
                    </div>
                `
                  )
                  .join("")}
            </div>
        `
        : "";

    body.innerHTML = `
            <div class="row">
                <div class="col-md-4">
                    <img src="${coverUrl}" class="game-detail-image w-100" alt="${
      game.title
    }"
                         onerror="this.src='https://via.placeholder.com/400x300?text=No+Cover'">
                </div>
                <div class="col-md-8">
                    <h5>${game.title}</h5>
                    
                    ${
                      game.moby_score
                        ? `
                        <p><strong>MobyGames Score:</strong> ${game.moby_score}/10</p>
                    `
                        : ""
                    }
                    
                    ${
                      game.release_date
                        ? `
                        <p><strong>Release Date:</strong> ${new Date(
                          game.release_date
                        ).toLocaleDateString()}</p>
                    `
                        : ""
                    }
                    
                    ${
                      game.platforms && game.platforms.length > 0
                        ? `
                        <p><strong>Platforms:</strong> ${game.platforms.join(
                          ", "
                        )}</p>
                    `
                        : ""
                    }
                    
                    ${
                      game.genres && game.genres.length > 0
                        ? `
                        <p><strong>Genres:</strong> ${game.genres.join(
                          ", "
                        )}</p>
                    `
                        : ""
                    }
                    
                    ${
                      game.developers && game.developers.length > 0
                        ? `
                        <p><strong>Developers:</strong> ${game.developers.join(
                          ", "
                        )}</p>
                    `
                        : ""
                    }
                    
                    ${
                      game.publishers && game.publishers.length > 0
                        ? `
                        <p><strong>Publishers:</strong> ${game.publishers.join(
                          ", "
                        )}</p>
                    `
                        : ""
                    }
                    
                    ${
                      game.description
                        ? `
                        <div class="mt-3">
                            <h6>Description</h6>
                            <p>${game.description}</p>
                        </div>
                    `
                        : ""
                    }
                    
                    ${criticsHtml}
                </div>
            </div>
        `;

    modal.show();
  }

  showLoading(show) {
    const spinner = document.getElementById("loadingSpinner");
    if (spinner) {
      spinner.style.display = show ? "block" : "none";
    }
  }

  showNotification(message, type = "info") {
    // Create notification element
    const notification = document.createElement("div");
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText =
      "top: 20px; right: 20px; z-index: 9999; min-width: 300px;";

    notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

    document.body.appendChild(notification);

    // Auto remove after 5 seconds
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 5000);
  }
}

// Global functions for HTML onclick handlers
function performMainSearch() {
  if (window.gameApp) {
    window.gameApp.performMainSearch();
  }
}

function performSearch() {
  const query = document.getElementById("searchQuery")?.value;
  if (query && window.gameApp) {
    window.gameApp.performSearch(query);
  }
}

function applyFilters() {
  if (window.gameApp) {
    window.gameApp.applyFilters();
  }
}

function clearFilters() {
  if (window.gameApp) {
    window.gameApp.clearFilters();
  }
}

// Initialize the app when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  window.gameApp = new GameQuestApp();
});
