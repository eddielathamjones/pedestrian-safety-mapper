# TUCSON STREET DEATHS - 12-PAGE ZINE

## What Is This?

A **print-ready, photocopier-friendly zine** about the 719 pedestrian deaths in Tucson from 1991-2022.

- **12 pages** of confrontational data visualization
- **Black & white** for easy photocopying
- **Punk DIY aesthetic** - copy it, share it, distribute it
- **Print-ready** - designed for US Letter (8.5" x 11")

## View It

**http://localhost:5000/zine**

(After running `python3 src/backend/app.py`)

## The 12 Pages

1. **COVER**: 719 DEAD - Your streets are killing machines
2. **THE CRISIS**: Fatalities doubled 2018-2022
3. **WHERE THEY DIED**: Map + 45% on principal arterials
4. **WHEN THEY DIED**: 6PM-10PM peak danger hours
5. **67% MID-BLOCK**: Died where no crosswalks exist
6. **DARKNESS KILLS**: 63% killed in dark conditions
7. **DEADLIEST STREETS**: Hot spot list with death counts
8. **2022: WORST YEAR**: 64 dead, one every 5.7 days
9. **THEY WERE PEOPLE**: Humanizing the statistics
10. **THIS IS NOT ACCEPTABLE**: Why streets kill (design failures)
11. **WHAT WE DEMAND**: 6 demands for Vision Zero
12. **TAKE ACTION**: Resources + call to action (back cover)

## How to Print

### OPTION 1: Standard Pages
1. Open http://localhost:5000/zine
2. Press **Ctrl+P** (or Cmd+P on Mac)
3. Enable "Print backgrounds"
4. Print all 12 pages
5. Staple or distribute as-is

### OPTION 2: Folded Booklet (Advanced)
1. Print pages strategically on 3 sheets (double-sided)
2. Fold in half
3. Staple along fold
4. Creates a booklet format

(See page 13 in the zine for detailed folding instructions)

### OPTION 3: Photocopier Distribution
1. Print one master copy
2. Take to any photocopier
3. Make as many copies as you need
4. **Designed for B&W copying** - high contrast, photocopier-friendly
5. Distribute freely - this is DIY

## Design Features

### Photocopier-Optimized
- High contrast black and white
- Bold typography (Bebas Neue, Anton, Courier)
- No gradients or complex graphics
- ASCII art and text-based data viz
- Heavy borders and solid fills

### Zine Aesthetic
- **Punk DIY**: Raw, unpolished, urgent
- **Text-heavy**: Data as weapon
- **Confrontational**: No soft language
- **Copy-friendly**: Designed to be reproduced

### Print Specs
- **Page size**: US Letter (8.5" x 11") - also works with A4
- **Margins**: 0.5" all sides
- **Color**: Black & white only
- **Resolution**: Text-based for infinite scaling
- **File size**: Minimal (HTML/CSS)

## What's Inside

### Data Visualizations
- ASCII map representation
- Text-based bar charts
- Timeline of deaths (skull grid)
- Hot spot street list
- Year-over-year trends
- Lighting condition breakdown

### Confrontational Messaging
- "YOUR STREETS ARE KILLING MACHINES"
- "THEY WERE PEOPLE" (not statistics)
- "THIS IS NOT ACCEPTABLE"
- "DEMAND BETTER"

### Call to Action
- Vision Zero demands
- City Council contact
- Organizing instructions
- Data sources for verification

## Use Cases

### For Activists
Print 100 copies. Hand them out at City Council meetings.

### For Community Organizers
Leave stacks at coffee shops, libraries, community centers.

### For Students
Distribute on campus. Start conversations about urban planning.

### For Vision Zero Advocates
Use as handout at events. Evidence for policy demands.

### For Anyone
Make people **uncomfortable**. That's the point.

## Distribution Ideas

- City Council meetings
- Community board meetings
- Coffee shops (with permission)
- Libraries
- Community centers
- University campuses
- Transit stops
- Street corners (where legal)
- Farmers markets
- Local events
- Mail to elected officials

## Legal & Ethics

### This is Open Source
- Copy freely
- Distribute freely
- Modify if needed
- No attribution required

### Data Source
- FARS (Fatality Analysis Reporting System)
- NHTSA (National Highway Traffic Safety Administration)
- Public data
- Verifiable facts

### Purpose
Educational. Advocacy. Public awareness. Policy change.

### Not
Commercial use. This is about saving lives, not making money.

## Technical Details

### Files
- `src/frontend/zine.html` - 12-page zine structure
- `src/frontend/css/zine.css` - Print-ready styling
- `src/backend/app.py` - Serves at `/zine` route

### Print CSS
- `@page` rules for proper page breaks
- `@media print` for print-specific styles
- High contrast forced for photocopiers
- Page-break-after on all pages

### Browser Compatibility
Works in any modern browser:
- Chrome/Edge: ✅
- Firefox: ✅
- Safari: ✅

## Export to PDF

### Method 1: Browser Print
1. Open http://localhost:5000/zine
2. Ctrl+P → Save as PDF
3. Share digitally or print later

### Method 2: Command Line (if you have wkhtmltopdf)
```bash
wkhtmltopdf http://localhost:5000/zine tucson-street-deaths.pdf
```

## Customization

Want to adapt this for your city?

### Quick Edits
1. Edit `zine.html` - change statistics
2. Update street names in "Deadliest Streets"
3. Change city name throughout
4. Adjust time ranges if needed

### Keep the Spirit
- Confrontational tone
- High contrast design
- Data as weapon
- DIY aesthetic
- Call to action

## Impact

### What This Does
- **Informs**: Raw data, no sugarcoating
- **Provokes**: Makes people uncomfortable
- **Mobilizes**: Clear demands, action items
- **Distributes**: Easy to copy and share

### What We Want
- Vision Zero commitment
- Protected crosswalks
- Street lighting
- Lower speed limits
- **ZERO DEATHS**

## The Message

**Streets that kill are a choice.**

**Demand better.**

---

## Print Now

1. Run the server: `python3 src/backend/app.py`
2. Open: http://localhost:5000/zine
3. Print: Ctrl+P
4. Distribute: Everywhere

**64 people died in 2022.**

**How many in 2023? 2024? 2025?**

**Make copies. Make noise. Make change.**

---

☠☠☠ COPY THIS. SHARE THIS. ACT ON THIS. ☠☠☠
