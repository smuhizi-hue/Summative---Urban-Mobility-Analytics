let selectedZone = null;
let currentPage = 1;
let sortorder = "desc";

const charts = {};
let map = null;
let zoneLayer = null;
let zoneStats = {};
let tooLittleData = 50;

const metricLabels = {
    pickups: "pickups",
    avg_fare: "avg fare ($)",
    tip_percent: "tip %",
    avg_speed: "avg speed (mph)",
    avg_distance: "avg distance (mi)",
};

function number(value) {
    if (value === null || value === undefined) return "-";
    return Number(value).toLocaleString();
}

function money(value) {
    if (value === null || value === undefined) return "-"; 
    return "$" + Number(value).toFixed(2);
}

function formatMetric(metric, value) {
    if (value === null || value === undefined) return "-";
    if (metric === "pickups") return number (value);
    if (metric === "avg_fare") return money (value);
    if (metric === "tip_percent") return value + "%";
    if (metric === "avg_speed") return value + "mph";
    return value + "mi";
}

function byID(id) {
    return documents.getElementbyID("map");
}

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error ("The server answered with an error for "+ url);
  return await response.json();    
}

//filters 
function getFilters() {
    const params = new URLSearchParams();

//input id name the api expects
const fields = [
    ["f-start", "start_date"], ["f-end", "end_date"], ["f-borough", "borough",]
    ["f-payment", "payment_type"], ["f-vendor", "vendor_id"], ["f-daytype", "day_type"],
    ["f-hour-from", "hour_from"], ["f-hour-to", "hour_to"],
    [ "f-min-distance", "min_distance"], ["f-max-distance", "max_distance"]
    ["f-min-fare", "min-fare"], ["f-max-fare", "max_fare"],
];
for(const field of fields) {
    const value = byID(field[0]).value;
    if (value !=="") params.set(field[1], value);
}
if (byID("f-aiport").checked) params.set("airport_only", "1");
if (byID("f-suspicious").checked) params.set ("hide_suspicious", "1");
if (selectedZone !== null) params.set("zone_id", selectedZone.id);
return params
}

function resetFilters() {
    const inputs = document.querySelectorAll(".filters input, .filters select");
    for (const input of inputs) {
        if (input.type === "checkbox") input.checked = false;
        else input.value = "";
    }
    clearZone();
}

function selectZone(id, name)  {
    selectedZone = { id: id, name: name};
    const chip = byID("Zone-chip");
    chip.textContent = "Zone: " + name + " ";
    chip.classList.remove("hidden");
    loadEverything();
}
function clearZone() {
    selectedZone = null;
    byID("zone-chip").classList.add("hidden");
}

async function loadOptions() {
    const options = await getJson("/api/options");

    for (const name of options.boroughs) {
        byID("f-borough").add(new Option(name, name));
    }
    for (const payment of options.payment_types) {
        byID("f-payment").add(new Option(payment.payment_type_name, payment.payment_type_id));
    }
    for (const id of ["f-start", "f-end"]) {
        byID(id).min = options.first_day;
        byID(id).max = options.last_day;

    for (const vendor of options.vendors){
        byID("f-vendor").add(
          new Option(vendor.vendor_name, vendor.vendor_id)
        );
    }
    }
}

//charts
function makecharts() {
    charts.defaults.font.family = "system-ui, sans-serif";
    const hours = [];
    for(let h = 0; h < 24; h++) hours.push(h + ":00");
    const lineoptions = (yTitle) = ({
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        scales: { y: { title: {display: true, text: yTitle}, beginAtZero: true} },
    });
    charts.hourly = new chart(byID("chart-hourly"), {
        type: "line",
        data: { labels: hours, datasets: [
            {label: "weekdays", data [], bordercolor: "#2563eb", backgroundcolor: "#2563eb", tension: 0.3},
            {label: "weekends", data [], bordercolor: "#f59e0b", backgroundcolor: "#f59e0b", tension: 0.3},
        ]}
        options: lineoptions("% of trips"),

    })
    charts.speed = new chart(byID("chart-speed"), {
        type: "line",
        data: { labels: hours, datasets: [
            {label: "weekdays", data: [], bordercolor: "#2563eb", backgroundcolor: "#2563eb", tension: 0.3},
            {label: "weekends", data: [], bordercolor: "#f59e0b", backgroundcolor: "#f59e0b"; tension: 0.3},


    ]}
    options: lineoptions("mph"),
    });

    charts.daily = new chart(byID("chart-daily"), {
        type: "bar",
        data: { labels: [], datasets: [{ label: "Trips", data [], backgroundcolor: "#ffc107"}] },
        options: { responsive: true, maintainAspectRatio: false, Plugins:{ legend: { display: false} } },
    });

    charts.payment = new charts(byID("chart-payments"), {
        type: "doughnut",
        data: { labels: [], datasets: [{ data [], backgroundcolor: ["#2563eb", "#ffc107", "#10b981", "#ef4444"] }] },
        options: { responsive: true , maintainAspectRatio: false },
    });

    charts.quality = new chart(byID(chart-quality), {
        type: "bar",
        data: { labels: [], datasets: [ { label: "Rows removed, data: [], backgroundcolor: "#ef4444"}] ],
        options: { indexAxis: "y", responsive: true, maintainAspectRatio: false, Plugins: { legend: {display: false} } },

    });
}

//loaders
async function loadkpis(query) {
    const k = await getJson("/api/kpis?" + query);
    byID("kpi-trips").textContent = number(k.trips);
    byID("kpi-fare").textContent = money(k.avg_fare);
    byID("kpi-distance").textContent = k.avg_distance === null ? "-" : k.avg_distance + " mi";
    byID("kpi-minutes").textContent = k.avg_minutes === null ? "-" : k.avg_minutes + " min";
    byID("kpi_speed").textContent = k.avg_speed === null ? "-" : k.avg_speed + "mph";
    byID("kpi-tip").textContent = k.tip_percent === null ? "-" : k.tip_percent + "%";
    byID("header-count").textContent = number(k.trips) + "trips selected";
}

async function loadHourly(query) {
    const rows = await getJson("/api/hourly?" + query);
    
    const totals = [0, 0];
    for (const row of rows) totals[row.is_weekend] += row.trips;

    const share = [new Array(24).fill(null), new Array(24).fill(null)];
    const speed = [new Array(24).fill(null), new Array(24).fill (null)];
    for (const row of rows) {
        share[row.is_weekend][row.hour] = Math.round(row.trips / totals [row.is_weekend] * 1000) /10;
        speed[row.is_weekend][row.hour] = row.avg_speed;
    }
         
    charts.hourly.data.datasets[0].data = share[0];
    charts.hourly.data.datasets[1].data = share[1];
    charts.hourly.update();
    charts.speed.data.datasets[0].data = speed[0];
    charts.speed.data.datasets[1].data =speed [1];
    charts.speed.update();
}

async function loadDaily (query) {
    const rows  = await getJson("/api/daily?" + query);
    charts.daily.data.labels = rows.map((r) => r.day.slice(5));
    charts.daily.data.datasets[0].data =rows.map((r) => r.trips);
    charts.daily.update();
}

async function loadpayments (query) {
    const rows = await getJson("/api/payments?" + query);
    charts.payment.data.labels = rows.map((r) = r.trips);
    charts.payment.data.datasets[0].data = rows.map((r) = r.trips);
    charts.payments.update();
}

async function loadRoutes(query) {
    const rows = await getJson("/api/routes/top?n=10&" + query);
    let html = "";
    rows.array.forEach((r,i) => {
        html +=  `<tr><td>${i + 1}</td><td>${r.pickup_zone}</td><td>${r.dropoff_zone}</td>
             <td>${number(r.trips)}</td></tr>`;
     });
    document.querySelector("#routes-table tbody").innerHTML = html;
}

async function loadTopZones(query) {
  const metric = byId("metric").value;
  const rows = await getJson("/api/zones/top?n=10&metric=" + metric + "&" + query);

  if (rows.length === 0) {
    byId("top-zones").innerHTML = "<li>No zone has enough trips for these filters.</li>";
    return;
  }
  const biggest = rows[0][metric];
  let html = "";
  for (const zone of rows) {
    const width = Math.max(4, zone[metric] / biggest * 100);
    html += `<li><div class="name">${zone.zone_name}</div>
             <div class="sub">${zone.borough} · ${formatMetric(metric, zone[metric])}</div>
             <div class="bar" style="width:${width}%"></div></li>`;
  }
  byId("top-zones").innerHTML = html;
}

async function loadTrips(query) {
  const url = "/api/trips?" + query + "&page=" + currentPage + "&sort_by=" + sortBy + "&order=" + sortOrder;
  const data = await getJson(url);

  let html = "";
  for (const t of data.rows) {
    html += `<tr><td>${t.pickup_time}</td><td>${t.pickup_zone}</td><td>${t.dropoff_zone}</td>
             <td>${t.trip_distance}</td><td>${t.trip_duration_min}</td><td>${t.avg_speed_mph}</td>
             <td>${money(t.fare_amount)}</td><td>${money(t.tip_amount)}</td>
             <td>${money(t.total_amount)}</td><td>${t.payment}</td></tr>`;
  }
  document.querySelector("#trips-table tbody").innerHTML = html;

  const lastPage = Math.max(1, Math.ceil(data.total / data.per_page));
  byId("trips-total").textContent = "(" + number(data.total) + " trips match)";
  byId("page-info").textContent = "Page " + data.page + " of " + number(lastPage);
  byId("btn-prev").disabled = currentPage <= 1;
  byId("btn-next").disabled = currentPage >= lastPage;
}

async function loadQuality() {
  const report = await getJson("/api/cleaning-report");
  byId("quality-text").textContent =
    number(report.rows_removed) + " raw records were removed and " + number(report.rows_kept) +
    " were kept (" + report.percent_kept + "%). " + number(report.suspicious_kept) +
    " kept records are marked as suspicious (their total does not match the sum of their parts).";
  charts.quality.data.labels = report.reasons.map((r) => r.reason.replaceAll("_", " "));
  charts.quality.data.datasets[0].data = report.reasons.map((r) => r.rows_removed);
  charts.quality.update();
}

// ============================================================ the map
async function makeMap() {
  map = L.map("map").setView([40.72, -73.95], 10);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors",
    opacity: 0.5,
  }).addTo(map);

  const shapes = await getJson("/api/zones/shapes");
  zoneLayer = L.geoJSON(shapes, {
    style: zoneStyle,
    onEachFeature: function (feature, layer) {
      layer.bindTooltip(() => tooltipText(feature));
      layer.on("click", () => selectZone(feature.properties.zone_id, feature.properties.zone_name));
    },
  }).addTo(map);
}

function tooltipText(feature) {
  const p = feature.properties;
  const s = zoneStats[p.zone_id];
  if (!s) return "<b>" + p.zone_name + "</b><br>" + p.borough + "<br>No trips";
  return "<b>" + p.zone_name + "</b><br>" + p.borough + "<br>" + number(s.pickups) + " pickups<br>" +
         "Avg fare " + money(s.avg_fare) + " · Tip " + (s.tip_percent === null ? "-" : s.tip_percent + "%") +
         "<br>Avg speed " + s.avg_speed + " mph";
}

// the colour scale: light yellow (low) to dark brown (high)
const palette = ["#fff7bc", "#fec44f", "#fe9929", "#d95f0e", "#993404"];
let scale = { min: 0, max: 1 };

function zoneStyle(feature) {
  const metric = byId("metric").value;
  const s = zoneStats[feature.properties.zone_id];
  let color = "#e2e8f0";                                  // grey = no / too little data
  if (s && s.pickups >= tooLittleData && s[metric] !== null) {
    let t = (s[metric] - scale.min) / (scale.max - scale.min || 1);
    if (metric === "pickups") t = Math.sqrt(s.pickups / scale.max);   // sqrt: so busy zones do not hide the rest
    t = Math.min(Math.max(t, 0), 1);
    color = palette[Math.min(Math.floor(t * 5), 4)];
  }
  return { fillColor: color, fillOpacity: 0.85, color: "#555", weight: 0.6 };
}

async function loadMap(query) {
  const rows = await getJson("/api/zones/stats?" + query);
  zoneStats = {};
  for (const row of rows) zoneStats[row.zone_id] = row;
  updateMapColors();
}

function updateMapColors() {
  const metric = byId("metric").value;

  // find the smallest and biggest value among zones with enough trips
  let min = Infinity;
  let max = -Infinity;
  for (const id in zoneStats) {
    const s = zoneStats[id];
    if (s.pickups >= tooLittleData && s[metric] !== null) {
      if (s[metric] < min) min = s[metric];
      if (s[metric] > max) max = s[metric];
    }
  }
  scale = { min: min, max: max };
  if (zoneLayer) zoneLayer.setStyle(zoneStyle);

  byId("legend").textContent = max === -Infinity ? "No data for these filters." :
    "Light = low (" + formatMetric(metric, min) + ")  →  dark = high (" + formatMetric(metric, max) +
    "). Grey = fewer than " + tooLittleData + " pickups.";
}

// ============================================================ put it all together
async function loadEverything() {
  byId("loading").classList.remove("hidden");
  currentPage = 1;
  const query = getFilters().toString();
  try {
    await Promise.all([
      loadKpis(query), loadHourly(query), loadDaily(query), loadPayments(query),
      loadMap(query), loadTopZones(query), loadRoutes(query), loadTrips(query),
    ]);
  } catch (error) {
    alert("Sorry, something went wrong: " + error.message);
  }
  byId("loading").classList.add("hidden");
}

// the three story cards at the top
function applyStory(which) {
  resetFilters();
  let target = "chart-hourly";
  if (which === "speed") target = "chart-speed";
  if (which === "airport") {
    byId("f-airport").checked = true;
    target = "kpi-fare";
  }
  loadEverything();
  byId(target).scrollIntoView({ behavior: "smooth", block: "center" });
}

// ============================================================ start
async function start() {
  makeCharts();
  await makeMap();                 // draw the map first: it only needs a file, not the database

  try {
    await loadOptions();           // fills the drop-downs (needs the database)
  } catch (error) {
    byId("header-count").textContent = "Database not reachable - is MySQL running?";
  }

  loadQuality().catch(function () {});   // if the database is down, just skip this chart
  loadEverything();

  byId("btn-apply").onclick = loadEverything;
  byId("btn-reset").onclick = function () { resetFilters(); loadEverything(); };
  byId("zone-chip").onclick = function () { clearZone(); loadEverything(); };

  byId("metric").onchange = function () {
    updateMapColors();
    loadTopZones(getFilters().toString());
  };

  byId("btn-prev").onclick = function () { currentPage--; loadTrips(getFilters().toString()); };
  byId("btn-next").onclick = function () { currentPage++; loadTrips(getFilters().toString()); };

  // click a column title to sort the trip table
  for (const th of document.querySelectorAll("#trips-table th[data-sort]")) {
    th.onclick = function () {
      const column = th.dataset.sort;
      if (sortBy === column) sortOrder = sortOrder === "desc" ? "asc" : "desc";
      else { sortBy = column; sortOrder = "desc"; }
      currentPage = 1;
      loadTrips(getFilters().toString());
    };
  }
}

start();

