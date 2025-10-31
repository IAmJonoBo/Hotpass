# Hotpass Web UI

Modern React-based web interface for Hotpass data pipeline monitoring and management.

## Features

- **Dashboard**: Real-time monitoring of pipeline runs with status and metrics
- **Lineage View**: Interactive data lineage visualization from OpenLineage/Marquez
- **Run Details**: Detailed view of individual runs with QA results
- **Admin Panel**: Configure API endpoints and environment settings
- **Dark Mode**: System-aware dark/light theme with manual toggle
- **Responsive Design**: Optimized for desktop (1024px+) with mobile support

## Tech Stack

- **React 18** - Latest React features
- **Vite** - Fast build tool and dev server
- **TypeScript** - Type-safe development
- **TailwindCSS** - Utility-first styling
- **shadcn/ui** - Accessible component primitives
- **React Query** - Server state management
- **React Router** - Client-side routing
- **Storybook** - Component documentation

## Getting Started

### Prerequisites

- Node.js 20+ and npm 10+
- Marquez backend (optional, mock data available)
- Prefect API (optional, mock data available)

### Installation

```bash
cd apps/web-ui
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3001](http://localhost:3001) in your browser.

### Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

### Storybook

View component documentation and test components in isolation:

```bash
npm run storybook
```

Open [http://localhost:6006](http://localhost:6006) to view the Storybook.

## Configuration

Configuration can be set via environment variables or the Admin page:

### Environment Variables

Create a `.env.local` file:

```env
VITE_PREFECT_API_URL=http://localhost:4200
VITE_MARQUEZ_API_URL=http://localhost:5000
VITE_ENVIRONMENT=local
```

### Admin Page

Navigate to `/admin` to configure API endpoints through the UI. Settings are stored in localStorage.

## Project Structure

```
apps/web-ui/
├── public/              # Static assets
├── src/
│   ├── api/            # API client functions
│   │   ├── marquez.ts  # Marquez/OpenLineage API
│   │   └── prefect.ts  # Prefect API
│   ├── components/     # React components
│   │   ├── ui/         # Base UI components
│   │   ├── Layout.tsx  # App layout wrapper
│   │   └── Sidebar.tsx # Navigation sidebar
│   ├── lib/            # Utility functions
│   │   └── utils.ts    # Helpers and utilities
│   ├── pages/          # Route pages
│   │   ├── Dashboard.tsx
│   │   ├── Lineage.tsx
│   │   ├── RunDetails.tsx
│   │   └── Admin.tsx
│   ├── stories/        # Storybook stories
│   ├── types/          # TypeScript type definitions
│   ├── App.tsx         # Root application component
│   ├── main.tsx        # Application entry point
│   └── index.css       # Global styles
├── .storybook/         # Storybook configuration
├── index.html          # HTML entry point
├── package.json        # Dependencies and scripts
├── tsconfig.json       # TypeScript configuration
├── vite.config.ts      # Vite configuration
└── tailwind.config.js  # Tailwind configuration
```

## Design System

### Colors

The UI uses a semantic color system that adapts to light/dark mode:

- **Primary**: Main brand color (indigo)
- **Secondary**: Secondary actions
- **Muted**: Subtle backgrounds and borders
- **Accent**: Highlights and interactive elements
- **Destructive**: Dangerous actions

### Typography

- **Headings**: Bold, tight tracking
- **Body**: Regular weight, comfortable line height
- **Code**: Monospace for technical content

### Components

All components follow shadcn/ui patterns:
- Composable and accessible
- Variants for different contexts
- Consistent spacing and sizing

## API Integration

### Marquez API

The app fetches lineage data from Marquez:

- Namespaces
- Jobs and job runs
- Datasets and their relationships
- Lineage graphs

Mock data is used when the API is unavailable.

### Prefect API

The app fetches flow data from Prefect:

- Flows and flow runs
- Deployments
- Run parameters and state

Mock data is used when the API is unavailable.

## Testing

Run linting:

```bash
npm run lint
```

Build for production (TypeScript check):

```bash
npm run build
```

## Future Enhancements

- [ ] Interactive lineage graph visualization (react-flow or d3)
- [ ] Real-time updates via WebSocket
- [ ] Search and filter across all runs
- [ ] Export functionality for reports
- [ ] Human-in-the-loop approval workflows
- [ ] Integration with Label Studio for data review
- [ ] Notification system for failed runs
- [ ] Custom dashboard widgets

## Integration with Hotpass CLI

The web UI is designed to complement the Hotpass CLI:

```bash
# Start Marquez backend
make marquez-up

# Run a pipeline
uv run hotpass refine --input-dir ./data --output-path ./dist/refined.xlsx

# View results in the web UI
npm run dev
```

## License

See repository root LICENSE file.
