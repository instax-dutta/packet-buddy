# PacketBuddy Dashboard Guide

## 1. Introduction to the Web Dashboard

The PacketBuddy Web Dashboard provides a beautiful, real-time visual interface for monitoring your network usage. Built with a modern **Liquid Glassmorphism** design, the dashboard offers instant insights into your bandwidth consumption, costs, and historical data patterns.

Key highlights:
- **Real-time speed monitoring** with live upload/download speeds
- **Usage analytics** with daily, monthly, and lifetime statistics
- **Cost calculations** to estimate data expenses
- **Interactive charts** powered by Chart.js
- **Responsive design** for desktop and mobile devices
- **Version**: v1.4.1

---

## 2. Accessing the Dashboard

The dashboard is accessible via any modern web browser once PacketBuddy is running.

### URL
```
http://127.0.0.1:7373/dashboard
```

### Prerequisites
- PacketBuddy must be running (the background service/daemon)
- The server listens on port `7373` by default
- No authentication required for local access

### Quick Start
1. Start PacketBuddy service
2. Open your browser
3. Navigate to `http://127.0.0.1:7373/dashboard`
4. The dashboard will automatically load and begin displaying data

---

## 3. Dashboard Sections

### 3.1 Live Speed Monitoring

The **Live Speed** card displays real-time network activity:

| Metric | Description |
|--------|-------------|
| **Upload Speed** | Current upload rate (B/s, KB/s, MB/s) |
| **Download Speed** | Current download rate (B/s, KB/s, MB/s) |
| **Progress Bars** | Visual indicators relative to current max speed |

**Features:**
- Updates every **2 seconds**
- Animated progress bars with gradient fills
- Purple accent for upload, teal for download
- Minimum scale of 1 MB/s for visual consistency

**API Endpoint:** `GET /api/live`

---

### 3.2 Today's Usage Overview

The **Today** card shows your cumulative usage for the current day:

| Metric | Description |
|--------|-------------|
| **Uploaded** | Total bytes uploaded today |
| **Downloaded** | Total bytes downloaded today |
| **Total Today** | Combined upload + download |
| **Est. Cost** | Estimated cost at ₹7.50/GB |

**Features:**
- Updates every **30 seconds**
- Displays current time in the header badge
- Shows either "This Device" or "Total Network" based on data source
- Cost calculation based on configurable rate

**API Endpoint:** `GET /api/today`

---

### 3.3 Monthly Usage Charts

The **Monthly Overview** section provides a bar chart visualization of daily usage:

**Features:**
- Navigate between months using arrow buttons
- Stacked bars showing upload (pink/purple) and download (teal)
- Y-axis automatically formats bytes (B, KB, MB, GB)
- Hover tooltips with detailed information

**Controls:**
- **← Previous Month**: Navigate to previous month
- **→ Next Month**: Navigate to next month
- Month label shows current selection (e.g., "February 2026")

**API Endpoint:** `GET /api/month?month=YYYY-MM`

---

### 3.4 Today's Distribution (Pie Chart)

A doughnut chart showing the upload vs. download ratio for today:

**Features:**
- 75% cutout design for modern aesthetics
- Legend showing percentage breakdown
- Upload shown in pink/purple
- Download shown in teal

**Legend displays:**
- Upload percentage
- Download percentage

---

### 3.5 Lifetime Statistics

The **Lifetime** card displays all-time usage across all devices:

| Metric | Description |
|--------|-------------|
| **Uploaded** | Total bytes uploaded (lifetime) |
| **Downloaded** | Total bytes downloaded (lifetime) |
| **Grand Total** | Combined lifetime usage |
| **Lifetime Cost** | Estimated total cost at ₹7.50/GB |

**Features:**
- Updates every **60 seconds**
- "All Devices" badge indicates aggregated data
- Supports global data stitching from multiple devices

**API Endpoint:** `GET /api/summary`

---

### 3.6 Cost Calculations

Cost estimates are displayed in multiple locations:

| Location | Field | Rate |
|----------|-------|------|
| Today Card | Est. Cost | ₹7.50/GB |
| Lifetime Card | Lifetime Cost | ₹7.50/GB |

**Note:** The cost rate is configurable in the PacketBuddy settings. Default is ₹7.50 per GB.

---

## 4. UI Features

### 4.1 Liquid Glassmorphism Design

The dashboard features a modern **Liquid Glassmorphism** aesthetic:

**Visual Elements:**
- Semi-transparent cards with blur backdrop (`backdrop-filter: blur(12px)`)
- Animated gradient background blobs
- Soft shadows and subtle borders
- Rounded corners (24px radius)
- Dark mode color scheme

**Color Palette:**
| Element | Color |
|---------|-------|
| Primary | Teal (`hsl(170, 70%, 42%)`) |
| Accent | Pink (`hsl(340, 60%, 60%)`) |
| Background | Dark (`hsl(0, 0%, 7%)`) |
| Card | Semi-transparent dark |
| Text | Light gray/white |

**Typography:**
- Font: **Nunito** (Google Fonts)
- Weights: 400, 600, 700, 800, 900
- Optimized for readability

---

### 4.2 Real-time Updates

The dashboard uses automatic polling intervals:

| Data Type | Refresh Interval |
|-----------|------------------|
| Live Speed | 2 seconds |
| Today Stats | 30 seconds |
| Lifetime Stats | 60 seconds |
| Clock | 1 second |

**Manual Refresh:**
- Click the **"Refresh Data"** button for immediate updates
- All data sections refresh simultaneously

---

### 4.3 Chart.js Visualizations

Charts are powered by **Chart.js v4.4.0** (loaded via CDN):

**Monthly Bar Chart:**
- Type: Grouped bar chart
- Responsive with maintainAspectRatio disabled
- Custom tooltip styling matching dashboard theme
- Y-axis callback for byte formatting

**Doughnut Chart:**
- Type: Doughnut (75% cutout)
- Hover offset animation (15px)
- Custom color scheme

---

### 4.4 Quick Actions Panel

The control panel provides quick action buttons:

| Button | Function |
|--------|----------|
| **🔄 Refresh Data** | Immediately refresh all dashboard data |
| **📥 Export CSV** | Download usage data as CSV file |
| **🎉 Year Wrap-Up** | Generate HTML year-in-review report |
| **🤖 LLM Export** | Export data optimized for LLM analysis |

---

### 4.5 Summary Statistics

Four summary cards at the bottom provide quick insights:

| Card | Description |
|------|-------------|
| **📈 Avg Daily Usage** | Estimated average daily usage (30-day calculation) |
| **⏱️ Peak Speed Today** | Highest combined speed recorded today |
| **📱 Active Devices** | Number of devices tracked |
| **💾 Data Points** | Number of days with recorded data in current month view |

---

## 5. Browser Compatibility

### Supported Browsers

| Browser | Minimum Version | Notes |
|---------|-----------------|-------|
| Chrome | 76+ | Full support |
| Firefox | 70+ | Full support |
| Safari | 14+ | Full support |
| Edge | 79+ | Full support |
| Opera | 63+ | Full support |

### Required Features
- **CSS Backdrop Filter**: Used for glassmorphism effect
- **CSS Grid**: Used for responsive layouts
- **CSS Custom Properties**: Used for theming
- **Fetch API**: Used for API calls
- **ES6+ JavaScript**: Arrow functions, async/await, template literals

### Known Limitations
- Internet Explorer is **not supported**
- Older browsers without backdrop-filter support will show solid backgrounds

---

## 6. Mobile Access

### Responsive Design

The dashboard is fully responsive and adapts to different screen sizes:

**Breakpoints:**
| Breakpoint | Layout Changes |
|------------|----------------|
| > 1024px | Full desktop layout with side-by-side charts |
| 768px - 1024px | Charts stack vertically |
| < 768px | Single column layout, stacked header |

**Mobile Optimizations:**
- Touch-friendly button sizes
- Simplified grid layouts
- Readable font sizes
- Collapsible elements where appropriate

### Accessing from Mobile Devices

To access the dashboard from a mobile device on the same network:

1. Find your computer's local IP address (e.g., `192.168.1.100`)
2. On your mobile device, navigate to: `http://192.168.1.100:7373/dashboard`
3. Ensure firewall allows connections on port 7373

**Note:** By default, PacketBuddy binds to `127.0.0.1` (localhost only). To enable network access, configure the server to bind to `0.0.0.0`.

---

## 7. Troubleshooting Dashboard Issues

### Dashboard Not Loading

| Issue | Solution |
|-------|----------|
| Connection refused | Ensure PacketBuddy service is running |
| Blank page | Check browser console for JavaScript errors |
| CORS errors | Access via correct URL (127.0.0.1:7373) |

### Charts Not Displaying

| Issue | Solution |
|-------|----------|
| Charts empty | Verify API endpoints return data (`/api/month`, `/api/today`) |
| Chart.js errors | Check internet connection (Chart.js loaded from CDN) |
| Wrong month data | Use month navigation buttons to refresh |

### Live Stats Not Updating

| Issue | Solution |
|-------|----------|
| Frozen values | Click "Refresh Data" button |
| All zeros | Check that network tracking is active |
| Intermittent updates | Check for browser resource throttling |

### Export Not Working

| Issue | Solution |
|-------|----------|
| CSV download fails | Check `/api/export?format=csv` endpoint directly |
| Year Wrap-Up blank | Ensure sufficient historical data exists |
| LLM Export error | Verify `/api/export/llm` endpoint is available |

### Performance Issues

| Issue | Solution |
|-------|----------|
| Slow updates | Reduce browser tab count, close other resource-heavy tabs |
| High CPU usage | Disable hardware acceleration in browser settings |
| Memory issues | Refresh the page periodically |

### Debug Mode

Open browser developer tools (F12) to:
- View API responses in Network tab
- Check JavaScript errors in Console tab
- Monitor refresh intervals and API calls

**Common Console Commands:**
```javascript
// Check API connectivity
fetch('http://127.0.0.1:7373/api/health').then(r => r.json()).then(console.log)

// Force data refresh
loadAllData()
```

---

## API Endpoints Reference

| Endpoint | Method | Description | Refresh Rate |
|----------|--------|-------------|--------------|
| `/api/health` | GET | Server health, hostname, version | On page load |
| `/api/live` | GET | Real-time speed data | 2 seconds |
| `/api/today` | GET | Today's usage statistics | 30 seconds |
| `/api/summary` | GET | Lifetime usage statistics | 60 seconds |
| `/api/month` | GET | Monthly daily breakdown | On demand |
| `/api/export?format=csv` | GET | Export data as CSV | Manual |
| `/api/export?format=json` | GET | Export data as JSON | Manual |
| `/api/export?format=html` | GET | Year wrap-up HTML report | Manual |
| `/api/export/llm` | GET | LLM-optimized export | Manual |

---

## Keyboard Shortcuts

The dashboard currently does not implement keyboard shortcuts. All interactions are mouse/touch-based through buttons.

---

## Additional Resources

- **Main Documentation**: See other wiki pages for installation and configuration
- **API Documentation**: See API-Reference.md for detailed endpoint specifications
- **Troubleshooting**: See Troubleshooting.md for general PacketBuddy issues
