# StudyNotesManager - Frontend

AI-powered learning management system frontend built with Next.js 14, TypeScript, and shadcn/ui.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript 5+
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **State Management**: Zustand
- **Data Fetching**: React Query (TanStack Query)
- **Forms**: React Hook Form + Zod
- **File Upload**: react-dropzone
- **Charts**: ECharts (echarts-for-react)
- **Mind Maps**: React Flow

## Getting Started

First, run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Environment Variables

Create a `.env.local` file:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_ENABLE_MINDMAP=true
NEXT_PUBLIC_ENABLE_QUIZ=true
NEXT_PUBLIC_ENABLE_ANALYTICS=true
```

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── page.tsx           # Dashboard (home)
│   ├── notes/             # Notes management
│   ├── mistakes/          # Mistakes bank
│   └── analytics/         # Analytics dashboard
├── components/
│   ├── ui/                # shadcn/ui components
│   ├── dashboard/         # Dashboard components
│   ├── notes/             # Notes components
│   ├── mindmap/           # Mind map visualization
│   ├── quiz/              # Quiz interface
│   ├── mistakes/          # Mistakes bank
│   ├── analytics/         # Analytics charts
│   ├── layout/            # Layout components
│   └── providers/         # React Query provider
├── hooks/                 # Custom React hooks
├── lib/                   # Utilities & API client
├── stores/                # Zustand stores
└── types/                 # TypeScript types
```

## Features

- **Dashboard**: Overview statistics, recent notes, activity calendar
- **Notes Management**: Upload, OCR, CRUD, search, and filtering
- **Mind Maps**: Interactive AI-generated knowledge visualization
- **Quiz System**: Multiple question types with real-time feedback
- **Mistakes Bank**: Review and learn from incorrect answers
- **Analytics**: Study time, accuracy trends, and activity heatmap
