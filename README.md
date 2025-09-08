# Global Trust Index (GTI)

An open data initiative that produces a credible, transparent, and updateable Global Trust Index using only programmatically accessible data sources.

## Overview

The Global Trust Index blends three pillars of trust measurement:

1. **Interpersonal Trust** - Survey data on whether "most people can be trusted"
2. **Institutional Trust** - Confidence in national government and institutions  
3. **Governance/Integrity Proxy** - Institutional quality measures (TI CPI, World Bank WGI)

All inputs are normalized to a 0-100 scale with data provenance and confidence flags.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ and npm
- Python 3.9+ and pip
- Make

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd trustindex
```

2. Copy environment configuration:
```bash
cp .env.example .env
```

3. Start services and initialize data:
```bash
make up
```

This command will:
- Start Docker services (Postgres, Redis, MinIO)
- Run database migrations
- Seed demo data
- Process sample CPI data

4. Start the development servers:
```bash
# Terminal 1: API server (port 3001)
make api

# Terminal 2: Web UI (port 3002)  
make web
```

5. Visit the application at http://localhost:3002

## Architecture

```
├── api/          # Fastify TypeScript API
├── web/          # Next.js React frontend
├── etl/          # Python ETL pipelines
├── db/           # Database migrations and schema
├── data/         # Raw data and staging files
├── scripts/      # Development utilities
└── .github/      # CI/CD workflows
```

## Development Commands

| Command | Description |
|---------|-------------|
| `make up` | Boot all services, migrate DB, seed data |
| `make down` | Stop all Docker services |
| `make api` | Start API dev server (port 3001) |
| `make web` | Start web dev server (port 3002) |
| `make migrate` | Apply database migrations |
| `make seed` | Load demo data |
| `make etl-cpi` | Process CPI sample data |
| `make clean` | Clean containers and volumes |

## API Endpoints

- `GET /api/countries` - List countries with latest GTI scores
- `GET /api/score?year=YYYY&trust_type=core` - Per-country scores for specified year
- `GET /api/country/{iso3}?from=YYYY&to=YYYY` - Country time series with pillar breakdown
- `GET /api/methodology` - Current methodology and versioning info

## Data Sources

### Approved Sources (Open/Programmatic Access)
- World Values Survey (WVS)
- European Social Survey (ESS)  
- Regional Barometers (Afro/Arab/Latino/Asian)
- OECD Trust Indicators
- Transparency International CPI
- World Bank Worldwide Governance Indicators (WGI)

### GTI Calculation

Primary blend when all pillars are available:
```
GTI = 0.4 × INSTITUTIONAL + 0.3 × INTERPERSONAL + 0.3 × GOVERNANCE
```

Governance proxy combines:
```
GOVERNANCE = 0.5 × CPI + 0.5 × WGI_rescaled
```

### Confidence Tiers
- **A**: Current survey data (≤3y) + current governance proxy
- **B**: Survey >3y old OR only one pillar + governance proxy  
- **C**: Governance proxy only (no valid surveys within 7y)

## Database Schema

Key tables:
- `countries` - ISO3 codes, names, regions, income groups
- `observations` - Normalized trust data per source/year/country  
- `country_year` - Computed GTI scores and confidence tiers

## Testing

```bash
# API tests
cd api && npm test

# Web tests  
cd web && npm test

# ETL tests
cd etl && python -m pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes following the code style guidelines
4. Run tests and linting
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Code Style

- **TypeScript/JavaScript**: 2-space indentation, ES modules, camelCase
- **Python**: 4-space indentation, snake_case, Black formatting
- **SQL**: Lowercase keywords, one statement per migration

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Data Ethics

- All displayed values show source and year provenance
- Year-over-year changes >25 points are flagged for review
- Source licenses are stored and respected
- Data removal path available for license changes

## Support

For questions or issues, please:
1. Check existing [GitHub Issues](../../issues)
2. Review the [documentation](CLAUDE.md)
3. Open a new issue with detailed information