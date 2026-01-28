# CSS ANALYSIS REPORT - DUX FRONTEND
**Generated:** January 28, 2026
**Scope:** React Frontend (dux-front/src)

---

## EXECUTIVE SUMMARY

The Dux frontend uses 7 CSS files organized around a neo-brutalist design system. Analysis reveals:

- **Total CSS Files:** 7
- **Total CSS Classes Defined:** 303
- **Total Classes Used:** 249
- **Unused Classes:** 54 (18% unused)
- **CSS Variables Defined:** 62
- **CSS Variables Used:** 40
- **Unused CSS Variables:** 22 (35% unused)
- **Duplicate Class Definitions:** 13 (spanning multiple files)

### Key Findings:
1. **Significant CSS Duplication** between `home.css` and `jobOffersCard.css`
2. **Unused Components** in foundation CSS (`neo-brutalism.css`) suggest feature bloat
3. **Unused Profile Setup Styles** indicate incomplete implementation
4. **Color Variable Over-definition** in the design system (22 unused color shades)
5. **Media Query Duplication** across multiple files

---

## SECTION 1: CSS FILE STRUCTURE & IMPORTS

### Import Map

| CSS File | Size | Imports | Purpose |
|----------|------|---------|---------|
| **neo-brutalism.css** | 822 lines | main.tsx | Global design system, theme, components |
| **home.css** | 755 lines | Home.tsx, ProfileHub.tsx, WikiMetier.tsx, Settings.tsx | Home page grid layout, CV score card, profile hub |
| **job-detail.css** | 250 lines | JobDetail.tsx | Job detail modal styling |
| **wiki-metier.css** | 432 lines | WikiMetier.tsx | Job category/metier wiki layout |
| **detailedAnalysis.css** | 868 lines | DetailedAnalysis.tsx | CV analysis page layout |
| **profileSetup.css** | 212 lines | ProfileSetup.tsx | Profile setup form styling |
| **jobOffersCard.css** | 250 lines | JobOffersCard.tsx | Job offers carousel (duplicates home.css) |

### Classes by File

```
neo-brutalism.css:        54 classes (36 used, 18 unused)
home.css:                 61 classes (58 used, 3 unused)
job-detail.css:           19 classes (16 used, 3 unused)
wiki-metier.css:          49 classes (43 used, 6 unused)
detailedAnalysis.css:     83 classes (81 used, 2 unused)
profileSetup.css:         20 classes (5 used, 15 unused)
jobOffersCard.css:        17 classes (10 used, 7 unused)
```

---

## SECTION 2: UNUSED CSS CLASSES (54 Total)

### By File

#### neo-brutalism.css (18 unused - 33%)
These are design system components defined but never instantiated:

```
Line 59:  .8 (parsing artifact)
Line 266: .nb-btn--success (button variant - unused)
Line 202: .nb-card--flat (card variant - unused)
Line 198: .nb-card--muted (card variant - unused)
Line 166: .nb-container (layout container - unused)
Line 409: .nb-divider (divider element - unused)
Line 397: .nb-gap-lg (gap utility - unused)
Line 393: .nb-gap-sm (gap utility - unused)
Line 541: .nb-menu-toggle (mobile menu toggle - unused)
Line 507: .nb-nav-btn (navigation button - unused)
Line 529: .nb-nav-btn--active (active nav button - unused)
Line 578: .nb-nav-drawer (mobile drawer - unused)
Line 178: .nb-row (flexbox row - unused)
Line 206: .nb-segment (segment box - unused)
Line 184: .nb-spread (spread layout - unused)
Line 428: .nb-tab (tab component - unused)
Line 689: .nb-theme-btn (theme selector - unused)
Line 716: .nb-theme-btn--active (active theme - unused)
```

#### profileSetup.css (15 unused - 75%)
Most setup form styles are unused, suggesting incomplete implementation.

#### jobOffersCard.css (7 unused - 41%)
Complete duplicate of carousel styling from home.css.

---

## SECTION 3: DUPLICATE CLASS DEFINITIONS (13 Classes)

### Home.css ↔ JobOffersCard.css (9 Duplicates)
```
.carousel-btn, .carousel-container, .carousel-content, .carousel-indicators
.job-offers-carousel, .offer-label, .offer-label--concern, .offer-list, .offer-section
```

**Issue:** JobOffersCard.css has completely redundant carousel styling that duplicates home.css definitions.

---

## SECTION 4: CSS CUSTOM PROPERTIES (VARIABLES) ANALYSIS

### CSS Variables Summary
- **Total Defined:** 62 variables
- **Actually Used:** 40 variables
- **Unused:** 22 variables (35% waste)

### Top 20 Most-Used CSS Variables

| Variable | Usage Count |
|----------|-------------|
| `--nb-fg` | 67 |
| `--nb-border` | 44 |
| `--nb-radius` | 35 |
| `--nb-accent` | 20 |
| `--nb-transition` | 19 |
| `--nb-bg-muted` | 19 |
| `--nb-bg` | 16 |

### Unused CSS Variables (22 Total)
- Color palette over-definition (11 unused shades)
- Shadow system variables (4 - never used due to flat design)
- Miscellaneous artifacts (7 - `--active`, `--clamp`, `--clickable`, etc.)

---

## SECTION 7: REFACTORING RECOMMENDATIONS

### Priority 1: High Impact, Low Effort

#### 1.1 Delete jobOffersCard.css (URGENT)
- Complete duplicate of home.css carousel styles
- Consolidate carousel styling into home.css
- Update JobOffersCard.tsx imports
- **Effort:** 10 minutes

#### 1.2 Remove 18 Unused Classes from neo-brutalism.css
- Button/card variants: `.nb-btn--success`, `.nb-card--flat`, `.nb-card--muted`
- Layout utilities: `.nb-gap-lg`, `.nb-gap-sm`, `.nb-row`, `.nb-spread`, `.nb-divider`
- Navigation components (if not implementing responsive header)
- **Effort:** 15 minutes

#### 1.3 Delete or Complete profileSetup.css
- 75% unused classes indicate incomplete implementation
- Decision required: Is this feature active?
- If NO: Delete the file
- If YES: Implement missing styles
- **Effort:** 5 minutes (delete) or 2+ hours (complete)

### Priority 2: Medium Impact, Medium Effort

#### 2.1 Remove 22 Unused CSS Variables
- Consolidate color palette (remove unused shades)
- Remove shadow system (flat design doesn't use)
- Remove naming artifacts
- **Effort:** 20 minutes

#### 2.2 Standardize Media Query Breakpoints
- Multiple files use inconsistent breakpoints (768px vs 767px, 800px)
- Create shared breakpoint variables
- **Effort:** 30 minutes

#### 2.3 Minor Cleanup
- Remove 3 unused classes from home.css
- Remove 3 unused classes from job-detail.css
- Remove 6 unused classes from wiki-metier.css
- Remove 2 unused classes from detailedAnalysis.css
- **Effort:** 20 minutes

---

## SECTION 8: FILE HEALTH SCORES

| File | Score | Status | Action |
|------|-------|--------|--------|
| neo-brutalism.css | 7/10 | Needs cleanup | Remove 18 unused classes & 22 unused variables |
| home.css | 9/10 | Good | Minor cleanup (3 unused classes) |
| job-detail.css | 8/10 | Good | Minor cleanup (3 unused classes) |
| wiki-metier.css | 8/10 | Good | Minor cleanup (6 unused classes) |
| detailedAnalysis.css | 9/10 | Excellent | Minor cleanup (2 unused classes) |
| profileSetup.css | 3/10 | CRITICAL | Delete or complete implementation |
| jobOffersCard.css | 2/10 | CRITICAL | Delete (duplicate) |

---

## SECTION 9: METRICS SUMMARY

### Code Efficiency Metrics

```
Total CSS Lines:          3,588 lines
Lines Per Class:          12 lines/class (average)
CSS Classes:              303 (249 used, 54 unused = 18% waste)
CSS Variable Usage:       64% utilized (40 of 62)
Duplicate Classes:        13 (4.3% of all classes)
```

### Post-Cleanup Projections

```
After removing unused:
- CSS lines: 3,588 → ~3,150 (12% reduction)
- Unused classes: 54 → ~0-5 (future features)
- Unused variables: 22 → 0
- Duplicate files: 2 → 1
```

---

## IMPLEMENTATION ROADMAP

### Week 1 - Critical Issues
1. Delete `jobOffersCard.css` (5 min)
2. Update JobOffersCard.tsx imports (5 min)
3. Decide on ProfileSetup feature (decision required)
4. If inactive: delete `profileSetup.css` (2 min)

### Week 2 - Cleanup
5. Remove 18 unused classes from neo-brutalism.css
6. Remove 2 unused classes from detailedAnalysis.css
7. Remove 3 unused classes from job-detail.css
8. Remove 6 unused classes from wiki-metier.css
9. Remove 3 unused classes from home.css

### Week 3 - Optimization
10. Remove 22 unused CSS variables from neo-brutalism.css
11. Standardize media query breakpoints
12. Add dark mode to page-specific files (optional)

---

## CONCLUSION

The Dux frontend CSS is **generally well-organized** but needs cleanup:

**Critical Issues:**
- Delete `jobOffersCard.css` (complete duplicate)
- Delete or complete `profileSetup.css` (75% unused)

**Major Improvements:**
- Remove 54 unused classes (18% of all classes)
- Remove 22 unused variables (35% of all variables)
- Consolidate media query breakpoints

**Estimated cleanup time:** 2-3 hours for comprehensive refactoring

**Post-cleanup benefits:**
- Smaller CSS payload
- Clearer codebase organization
- Easier maintenance
- No unused code to maintain
