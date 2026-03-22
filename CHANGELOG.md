# Changelog

All notable changes to this project are documented in this file.

This project follows semantic versioning principles.

## [1.2.0] - 2026-03-22

### Added
- Investment cards now support position editing directly from the portfolio detail area.
- New position edit modal allows updating:
  - quantity (`miktar`)
  - total cost (`maliyet`)
- Backend support for updating `maliyet` via `PUT /api/yatirim/<id>`.

### Changed
- Portfolio detail card actions extended for monthly stock accumulation workflows.
- Minor UI improvements for investment card content alignment and readability.

## [1.1.0] - 2026-03-22

### Added
- Fixed-expense records can now be recategorized after creation (`PUT /api/sabit-gider/<id>`).
- Daily-expense records can now be recategorized after creation (`PUT /api/gunluk-gider/<id>`).
- Category edit UX upgraded from manual text input to dropdown-based modal selection.
- New fixed-expense category for one-time large expenses (`tek_seferlik`).
- Optional month/year inputs on fixed-expense create form.

### Changed
- Improved alignment and responsiveness for multiple form/table sections:
  - `Gelirler` form type alignment
  - `Kredi Kartı` category alignment
  - `Taksitler` installment input alignment
  - `Yatırımlar` portfolio card text/value layout
- Improved category mapping and label consistency in list views.

### Privacy
- Privacy mode remains enabled by default (`PRIVACY_MODE=1`) and blocks user-URL based external product scraping.

## [1.0.0] - 2026-03-22

### Added
- Initial public release of Finora.
- Branding update to **Finora** and custom favicon.
- Rule-based Turkish AI assistant for finance entry/update flows.
- Investment module with live price update and fallback sources.
- Dashboard and module-level responsive UI improvements.
- Baseline privacy controls and `.gitignore` hardening.
- Professional project documentation (`README.md`).
