/**
 * DAA Benchmark & Travel-Time Visualizations with Chart.js
 */

let travelTimeChartInstance = null;
let nodeExplorationChartInstance = null;

function renderBenchmarkCharts(benchmarkData) {
    if (!benchmarkData || benchmarkData.length === 0) return;

    const labels = benchmarkData.map(b => b.name);
    const times = benchmarkData.map(b => b.time_min || 0);
    const visitedCounts = benchmarkData.map(b => b.visited_nodes || 0);
    const relaxations = benchmarkData.map(b => b.relaxations || 0);

    // Color mapping
    const timeColors = benchmarkData.map(b => {
        if (b.name.includes("Traffic")) return "#10b981"; // Emerald for optimal
        if (b.name.includes("A*")) return "#06b6d4";      // Cyan
        if (b.name.includes("Distance")) return "#ef4444";// Red
        return "#f59e0b";                                 // Amber for Greedy
    });

    // 1. Travel Time Chart
    const timeCtx = document.getElementById("travelTimeChart");
    if (timeCtx) {
        if (travelTimeChartInstance) {
            travelTimeChartInstance.destroy();
        }

        travelTimeChartInstance = new Chart(timeCtx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [{
                    label: "Estimated Travel Time (Minutes)",
                    data: times,
                    backgroundColor: timeColors,
                    borderRadius: 6,
                    borderWidth: 1,
                    borderColor: "rgba(255,255,255,0.2)"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` ${ctx.raw} minutes`
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: "rgba(255, 255, 255, 0.08)" },
                        ticks: { color: "#9ca3af" },
                        title: {
                            display: true,
                            text: "Travel Time (min)",
                            color: "#9ca3af"
                        }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: "#d1d5db", font: { size: 11 } }
                    }
                }
            }
        });
    }

    // 2. Search Space (Explored Nodes) Chart
    const nodeCtx = document.getElementById("nodeExplorationChart");
    if (nodeCtx) {
        if (nodeExplorationChartInstance) {
            nodeExplorationChartInstance.destroy();
        }

        nodeExplorationChartInstance = new Chart(nodeCtx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Nodes Visited (Search Space)",
                        data: visitedCounts,
                        backgroundColor: "#8b5cf6",
                        borderRadius: 6
                    },
                    {
                        label: "Edge Relaxations",
                        data: relaxations,
                        backgroundColor: "#3b82f6",
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        labels: { color: "#d1d5db", font: { size: 11 } }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: "rgba(255, 255, 255, 0.08)" },
                        ticks: { color: "#9ca3af" }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: "#d1d5db", font: { size: 11 } }
                    }
                }
            }
        });
    }
}
