(() => {
  const canvas = document.getElementById("star-history-chart");

  // This script is included site-wide, but should only run on this page.
  if (!canvas) {
    return;
  }

  const totalElement = document.getElementById("star-history-total");
  const statusElement = document.getElementById("star-history-status");

  const dataUrl =
    `https://raw.githubusercontent.com/` +
    `leggedrobotics/pace-sim2real/` +
    `star-history-data/star-history.json?ts=${Date.now()}`;

  let chart = null;

  function themeColors() {
    const isDark =
      document.body.getAttribute("data-md-color-scheme") === "slate";

    return {
      text: isDark ? "#c9d1d9" : "#57606a",
      grid: isDark
        ? "rgba(201, 209, 217, 0.14)"
        : "rgba(87, 96, 106, 0.16)",
      line: "#0F70B7",
      fillTop: isDark
        ? "rgba(15, 112, 183, 0.42)"
        : "rgba(15, 112, 183, 0.30)",
      fillBottom: "rgba(15, 112, 183, 0.02)",
    };
  }

  function formatDate(timestamp, detailed = false) {
    return new Intl.DateTimeFormat(
      "en",
      detailed
        ? {
            day: "numeric",
            month: "short",
            year: "numeric",
          }
        : {
            month: "short",
            year: "numeric",
          },
    ).format(new Date(timestamp));
  }

  function applyTheme() {
    if (!chart) {
      return;
    }

    const colors = themeColors();

    chart.options.scales.x.ticks.color = colors.text;
    chart.options.scales.y.ticks.color = colors.text;
    chart.options.scales.x.grid.color = colors.grid;
    chart.options.scales.y.grid.color = colors.grid;

    chart.update("none");
  }

  async function renderChart() {
    if (typeof Chart === "undefined") {
      throw new Error("Chart.js was not loaded.");
    }

    const response = await fetch(dataUrl, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(
        `Could not load star-history data: HTTP ${response.status}`,
      );
    }

    const history = await response.json();

    if (!Array.isArray(history.stars) || history.stars.length === 0) {
      throw new Error("The star-history JSON contains no data points.");
    }

    const points = history.stars.map((point) => ({
      x: Date.parse(`${point.date}T00:00:00Z`),
      y: point.count,
    }));

    const context = canvas.getContext("2d");
    const colors = themeColors();

    const gradient = context.createLinearGradient(
      0,
      0,
      0,
      canvas.parentElement.clientHeight || 500,
    );

    gradient.addColorStop(0, colors.fillTop);
    gradient.addColorStop(1, colors.fillBottom);

    chart = new Chart(context, {
      type: "line",

      data: {
        datasets: [
          {
            label: "GitHub stars",
            data: points,
            parsing: false,
            borderColor: colors.line,
            backgroundColor: gradient,
            borderWidth: 3,
            fill: true,
            tension: 0.18,
            cubicInterpolationMode: "monotone",
            pointRadius: 0,
            pointHoverRadius: 5,
            pointHoverBorderWidth: 2,
          },
        ],
      },

      options: {
        responsive: true,
        maintainAspectRatio: false,
        normalized: true,

        interaction: {
          mode: "nearest",
          intersect: false,
          axis: "x",
        },

        plugins: {
          legend: {
            display: false,
          },

          tooltip: {
            displayColors: false,

            callbacks: {
              title(items) {
                return formatDate(items[0].parsed.x, true);
              },

              label(context) {
                return `${context.parsed.y.toLocaleString()} stars`;
              },
            },
          },
        },

        scales: {
          x: {
            type: "linear",

            grid: {
              color: colors.grid,
            },

            ticks: {
              color: colors.text,
              maxTicksLimit: 7,

              callback(value) {
                return formatDate(Number(value));
              },
            },

            title: {
              display: true,
              text: "Date",
              color: colors.text,
            },
          },

          y: {
            beginAtZero: true,
            grace: "5%",

            grid: {
              color: colors.grid,
            },

            ticks: {
              color: colors.text,
              precision: 0,
            },

            title: {
              display: true,
              text: "Cumulative stars",
              color: colors.text,
            },
          },
        },
      },
    });

    totalElement.textContent = history.total_stars.toLocaleString();

    statusElement.textContent =
      `Updated ${formatDate(Date.parse(`${history.as_of}T00:00:00Z`), true)}`;
  }

  renderChart().catch((error) => {
    console.error(error);
    statusElement.textContent =
      "The star-history chart could not be loaded.";
  });

  // Update text and grid colors when the Material theme changes.
  const themeObserver = new MutationObserver(applyTheme);

  themeObserver.observe(document.body, {
    attributes: true,
    attributeFilter: ["data-md-color-scheme"],
  });
})();
