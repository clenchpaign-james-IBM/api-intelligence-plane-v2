# IBM Carbon Design System Migration

## Overview

This document describes the migration of the API Intelligence Plane frontend from Tailwind CSS to IBM Carbon Design System v11.

## Migration Date

March 12, 2026

## Changes Made

### 1. Package Dependencies

**Added:**
- `@carbon/react@^1.65.0` - Core Carbon React components
- `@carbon/styles@^1.65.0` - Carbon design tokens and styles
- `@carbon/icons-react@^11.49.0` - Carbon icon library
- `@carbon/charts@^1.19.0` - Carbon charts library
- `@carbon/charts-react@^1.19.0` - Carbon charts React wrapper
- `sass@^1.80.0` - SASS compiler for Carbon styles

**Removed:**
- `tailwindcss` - Replaced by Carbon styles
- `autoprefixer` - No longer needed
- `postcss` - No longer needed
- `lucide-react` - Replaced by Carbon icons
- `recharts` - Replaced by Carbon charts

### 2. Configuration Files

**Modified:**
- `frontend/package.json` - Updated dependencies
- `frontend/src/index.css` - Replaced Tailwind imports with Carbon styles

**Removed:**
- `frontend/tailwind.config.ts` - No longer needed
- `frontend/postcss.config.js` - No longer needed

### 3. Core Application Components

#### App.tsx
- Replaced custom navigation with Carbon UI Shell components:
  - `Header` - Main application header
  - `HeaderContainer` - Container for header with state management
  - `HeaderName` - Application name/logo
  - `HeaderNavigation` - Navigation menu container
  - `HeaderMenuItem` - Individual navigation items
  - `HeaderGlobalBar` - Global actions area
  - `HeaderGlobalAction` - Individual global actions
  - `SkipToContent` - Accessibility skip link
  - `Content` - Main content wrapper
  - `Theme` - Theme provider (using g10 theme)

#### Common Components

**Button.tsx**
- Wrapped Carbon `Button` component
- Maintained API compatibility with previous implementation
- Maps custom variants to Carbon kinds:
  - `primary` → `primary`
  - `secondary` → `secondary`
  - `danger` → `danger`
  - `ghost` → `ghost`

**Card.tsx**
- Wrapped Carbon `Tile` component
- Added custom header and footer support
- Uses Carbon spacing tokens for padding
- Maintains previous API for backward compatibility

**Loading.tsx**
- Wrapped Carbon `Loading` and `InlineLoading` components
- Supports full-screen overlay mode
- Uses Carbon loading indicators

**Error.tsx**
- Wrapped Carbon `InlineNotification` component
- Maps custom types to Carbon kinds:
  - `error` → `error`
  - `warning` → `warning`
  - `info` → `info`
- Maintains retry action support

### 4. Styling Approach

**Carbon Design Tokens:**
- Colors: `var(--cds-text-primary)`, `var(--cds-layer-01)`, etc.
- Spacing: `var(--cds-spacing-03)`, `var(--cds-spacing-05)`, etc.
- Typography: `cds--type-heading-03`, `cds--type-body-01`, etc.

**Theme:**
- Using Carbon's `g10` (Gray 10) theme
- Provides light theme with good contrast
- Can be switched to `g90`, `g100`, or `white` themes

### 5. Icons

Carbon icons are now used instead of Lucide React:
- `Notification` - For notifications
- `UserAvatar` - For user profile
- Additional icons available from `@carbon/icons-react`

### 6. Charts

Carbon Charts will replace Recharts for data visualization:
- More consistent with Carbon design language
- Better accessibility support
- Native integration with Carbon themes

## Benefits

1. **Enterprise-Grade Design**: IBM's design system used by Fortune 500 companies
2. **Accessibility**: WCAG 2.1 AA compliant out of the box
3. **Consistency**: Unified design language across all components
4. **Dark Mode**: Built-in theme switching support
5. **Performance**: Optimized component library
6. **Documentation**: Comprehensive documentation and examples
7. **Maintenance**: Active development and support from IBM

## Migration Status

### Completed ✅
- [x] Package dependencies updated
- [x] Carbon styles configured
- [x] App.tsx migrated to Carbon UI Shell
- [x] Common components migrated (Button, Card, Loading, Error)
- [x] Tailwind configuration removed
- [x] Page components migration (Dashboard, APIs, Gateways, Predictions, Optimization, Query)
- [x] Form components migration (AddGatewayForm, QueryInput)
- [x] Chart components migration to Carbon Charts (HealthChart, FactorsChart, RateLimitChart)
- [x] Table components migration to Carbon DataTable
- [x] Modal/Dialog components migration
- [x] UI polish and spacing improvements across all pages
- [x] Complete testing and validation

### UI Improvements Completed ✅
- [x] Dashboard page - Enhanced spacing, borders, and visual hierarchy
- [x] APIs page - Increased gaps, better alignment, professional appearance
- [x] Predictions page - Fixed dense layout, added proper spacing between items
- [x] Optimization page - Fixed recommendation spacing, migrated RateLimitPolicy to Carbon
- [x] Query page - Fixed Send button alignment and page scroll issues
- [x] All components now use Carbon design tokens and components
- [x] Removed all Tailwind CSS classes
- [x] Consistent spacing using Carbon spacing scale (spacing-03 to spacing-08)

## Migration Complete! 🎉

All components have been successfully migrated from Tailwind CSS to IBM Carbon Design System v11.

### Key Achievements

1. ✅ **Complete Component Migration**: All pages and components now use Carbon components
2. ✅ **Professional UI**: Enterprise-grade appearance with proper spacing and visual hierarchy
3. ✅ **Consistent Design**: Unified design language using Carbon design tokens
4. ✅ **Accessibility**: WCAG 2.1 AA compliant components
5. ✅ **Performance**: Optimized Carbon components for better performance
6. ✅ **Maintainability**: Clean, consistent codebase using Carbon patterns

### Spacing Standards Established

- **Between sections**: 40px (spacing-08)
- **Between cards**: 32px (spacing-07)
- **Card internal padding**: 24-32px (spacing-06 to spacing-07)
- **Between UI elements**: 16-24px (spacing-04 to spacing-06)
- **Tight spacing**: 12px (spacing-03) for related items

### Next Steps (Optional Enhancements)

1. **Dark Mode**: Implement theme switching (g10 ↔ g90/g100)
2. **Advanced Charts**: Explore additional Carbon Charts features
3. **Animations**: Add Carbon motion patterns for enhanced UX
4. **Responsive Design**: Further optimize for mobile devices
5. **Documentation**: Create component usage guide with Carbon examples

## Resources

- [Carbon Design System](https://carbondesignsystem.com/)
- [Carbon React Components](https://react.carbondesignsystem.com/)
- [Carbon Icons](https://www.carbondesignsystem.com/guidelines/icons/library/)
- [Carbon Charts](https://charts.carbondesignsystem.com/)
- [Carbon Themes](https://carbondesignsystem.com/guidelines/themes/overview/)

## Breaking Changes

### Component API Changes

Some component APIs have changed slightly:

**Button:**
- `variant` prop still supported but maps to Carbon's `kind`
- Loading state simplified (no spinner animation)

**Card:**
- Now uses Carbon Tile internally
- Styling uses Carbon design tokens instead of Tailwind classes

**Error:**
- Now uses InlineNotification
- `details` prop added for error object support

### Styling Changes

- All Tailwind utility classes must be replaced with:
  - Carbon design tokens (CSS variables)
  - Carbon utility classes
  - Inline styles using Carbon tokens

## Rollback Plan

If issues arise, the migration can be rolled back by:

1. Reverting `package.json` to previous version
2. Restoring Tailwind configuration files
3. Reverting component changes
4. Running `npm install` to restore previous dependencies

## Support

For questions or issues related to the Carbon migration, please:
1. Check Carbon documentation
2. Review Carbon React Storybook examples
3. Consult the Carbon community on GitHub

---

**Migration Lead**: Bob (Carbon-Adopter Mode)
**Migration Started**: March 12, 2026
**Migration Completed**: March 13, 2026
**Total Duration**: 1 day