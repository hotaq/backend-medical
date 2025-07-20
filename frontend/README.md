# 🏥 Medical Triage-BOTS Frontend

A modern React/Next.js frontend application for the Medical Triage-BOTS system with integrated LLM capabilities and real-time database connectivity.

## 🚀 Features

### Core Functionality
- **Multi-Modal Triage Submission** - Submit cases with text, images, and structured medical data
- **Real-Time Dashboard** - Live system metrics and case monitoring
- **LLM Integration** - Direct chat interface with medical AI assistant
- **Database Visualization** - Browse and analyze historical triage cases
- **Responsive Design** - Works seamlessly on desktop, tablet, and mobile

### AI-Powered Features
- **Medical Chat Assistant** - Ask questions about symptoms, conditions, and system status
- **Smart Case Analysis** - AI-powered triage scoring with detailed explanations
- **Multi-Modal Processing** - Text, image, and structured data analysis
- **Real-Time Results** - Live updates during case processing

### Technical Features
- **TypeScript** - Full type safety throughout the application
- **React Query** - Efficient data fetching and caching
- **Framer Motion** - Smooth animations and transitions
- **Tailwind CSS** - Modern, responsive design system
- **Form Validation** - Comprehensive form handling with react-hook-form
- **File Upload** - Drag-and-drop medical image uploads

## 🛠️ Technology Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with custom medical theme
- **State Management**: React Query (TanStack Query)
- **Forms**: React Hook Form with validation
- **UI Components**: Headless UI, Radix UI
- **Icons**: Heroicons
- **Charts**: Recharts
- **Animations**: Framer Motion
- **File Upload**: React Dropzone
- **Notifications**: React Hot Toast

## 📋 Prerequisites

- Node.js 18+ 
- npm 8+ or yarn 1.22+
- Medical Triage-BOTS Backend running on `http://localhost:8000`

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository (if not already done)
cd backend/frontend

# Install dependencies
npm install
# or
yarn install
```

### 2. Environment Setup

Create a `.env.local` file in the frontend directory:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Development Settings
NODE_ENV=development
NEXT_PUBLIC_ENV=development

# Optional: Analytics and monitoring
NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id
```

### 3. Start Development Server

```bash
# Start the development server
npm run dev
# or
yarn dev
```

The application will be available at `http://localhost:3000`.

### 4. Verify Backend Connection

1. Ensure the Medical Triage-BOTS backend is running on `http://localhost:8000`
2. Check the system health at `http://localhost:3000` - the status indicator should show "System Healthy"
3. Test the API connection in the browser console - `window.apiService` should be available

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx         # Root layout with providers
│   │   ├── page.tsx           # Homepage (Dashboard)
│   │   └── triage/
│   │       └── page.tsx       # Triage submission page
│   ├── components/            # Reusable UI components
│   │   └── Layout.tsx         # Main application layout
│   ├── pages/                 # Page components
│   │   ├── index.tsx          # Dashboard with LLM chat
│   │   └── triage.tsx         # Triage case submission
│   ├── services/              # API and external services
│   │   └── api.ts             # Backend API integration
│   ├── types/                 # TypeScript type definitions
│   │   └── medical.ts         # Medical data types
│   ├── hooks/                 # Custom React hooks
│   ├── styles/                # Global styles and Tailwind
│   │   └── globals.css        # Global CSS with medical theme
│   └── utils/                 # Utility functions
├── public/                    # Static assets
├── package.json              # Dependencies and scripts
├── tailwind.config.js        # Tailwind CSS configuration
├── tsconfig.json             # TypeScript configuration
└── next.config.js            # Next.js configuration
```

## 🎨 UI/UX Features

### Medical Theme
- **Color Scheme**: Medical blue (#0ea5e9) primary with urgency-based colors
- **Typography**: Inter font family for readability
- **Components**: Custom medical-themed UI components
- **Responsive**: Mobile-first design with tablet and desktop optimizations

### Urgency Level Visualization
- **Critical**: Red theme (#ef4444) - Immediate attention
- **High**: Orange theme (#f97316) - Urgent care
- **Medium**: Yellow theme (#f59e0b) - Semi-urgent
- **Low**: Green theme (#10b981) - Routine care

### Interactive Elements
- **Real-time Charts**: Case distribution and processing metrics
- **Progress Indicators**: Step-by-step triage submission
- **Loading States**: Smooth loading animations
- **Error Handling**: User-friendly error messages

## 🔌 API Integration

### Backend Endpoints Used
- `GET /` - System status
- `GET /health` - Health check
- `GET /metrics` - Performance metrics
- `POST /triage` - Submit triage case (JSON)
- `POST /triage/multipart` - Submit with file uploads
- `POST /chat` - Send message to LLM
- `GET /database/cases` - Get case list
- `GET /analytics/dashboard` - Dashboard data

### Data Flow
1. **User Input** → Form validation → API request
2. **Backend Processing** → ChiefBOT coordination → Database storage
3. **Response** → UI update → Notification → State management

## 💬 LLM Integration

### Medical Chat Assistant
The frontend includes a built-in chat interface that connects to the backend's LLM capabilities:

**Features:**
- Medical question answering
- System status inquiries
- Case-specific context
- Quick question buttons
- Response history

**Example Interactions:**
```
User: "What are the symptoms of diabetes?"
AI: "Diabetes symptoms typically include increased thirst, frequent urination, unexplained weight loss..."

User: "Show me system health"
AI: "Current system status: All components operational, average processing time 2.3 seconds..."
```

## 📊 Dashboard Features

### Real-Time Metrics
- **Total Cases**: Daily case count with trends
- **Critical Cases**: Emergency cases requiring immediate attention
- **Processing Time**: Average system performance
- **Success Rate**: System reliability metrics

### Interactive Charts
- **Hourly Cases**: Area chart showing case volume throughout the day
- **Urgency Distribution**: Pie chart of case priorities
- **Agent Performance**: Bar chart of processing times by agent

### System Monitoring
- **Health Status**: Real-time component status
- **Performance Metrics**: Live system statistics
- **Recent Activity**: Latest cases and system events

## 🩺 Triage Case Submission

### Multi-Step Form
1. **Patient Information** - Demographics and identifiers
2. **Symptoms & History** - Text-based medical information
3. **Medical Data** - Structured lab results and vital signs
4. **Images** - Medical image uploads with drag-and-drop
5. **Results** - AI analysis results and recommendations

### Data Types Supported
- **Text Data**: Symptoms, complaints, medical history
- **Structured Data**: Blood tests, vital signs, lab results
- **Images**: Retinal photos, X-rays, CT scans, MRI, ultrasound
- **Mixed Cases**: Any combination of the above

### File Upload Features
- **Drag & Drop**: Intuitive file upload interface
- **Image Preview**: Thumbnail previews of uploaded images
- **File Validation**: Type and size checking
- **Progress Tracking**: Upload progress indicators

## 🧪 Development

### Available Scripts

```bash
# Development
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server

# Code Quality
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript compiler
npm test             # Run Jest tests
npm run test:watch   # Run tests in watch mode

# Utilities
npm run clean        # Clean build artifacts
```

### Development Guidelines

1. **TypeScript**: All new code must be typed
2. **Components**: Use functional components with hooks
3. **Styling**: Use Tailwind CSS classes, avoid custom CSS
4. **Forms**: Use react-hook-form for form handling
5. **API**: Use React Query for data fetching
6. **Testing**: Write tests for complex logic

### Code Style
- **Prettier**: Automatic code formatting
- **ESLint**: Code quality and consistency
- **TypeScript**: Strict type checking
- **Imports**: Absolute imports using `@/` prefix

## 🔧 Configuration

### Environment Variables
```env
# Required
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional
NEXT_PUBLIC_ANALYTICS_ID=GA_TRACKING_ID
NEXT_PUBLIC_ENV=development|staging|production
```

### Tailwind Customization
The project includes a custom medical theme in `tailwind.config.js`:
- Medical color palette
- Urgency-specific colors
- Custom animations
- Medical-themed utilities

### Next.js Configuration
- API proxy to backend
- Security headers
- Image optimization
- TypeScript support

## 🚀 Deployment

### Production Build
```bash
# Build the application
npm run build

# Start production server
npm run start
```

### Environment Setup
1. Set `NEXT_PUBLIC_API_URL` to your production backend URL
2. Configure any analytics or monitoring services
3. Set up proper CORS on the backend for your frontend domain

### Docker Deployment
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## 🛠️ Troubleshooting

### Common Issues

1. **Backend Connection Failed**
   - Check if backend is running on `http://localhost:8000`
   - Verify CORS configuration
   - Check network connectivity

2. **File Upload Not Working**
   - Ensure backend supports multipart/form-data
   - Check file size limits
   - Verify image format support

3. **LLM Chat Not Responding**
   - Check backend chat endpoint
   - Verify API key configuration
   - Monitor browser console for errors

4. **Build Errors**
   - Run `npm run type-check` to identify TypeScript issues
   - Clear `.next` directory and rebuild
   - Check for dependency conflicts

### Performance Optimization
- **React Query**: Efficient caching and background updates
- **Image Optimization**: Next.js automatic image optimization
- **Code Splitting**: Automatic page-based code splitting
- **Bundle Analysis**: Use `npm run analyze` to check bundle size

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Write** tests if applicable
5. **Run** linting and type checking
6. **Submit** a pull request

### Development Workflow
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and test
npm run dev
npm run lint
npm run type-check

# Commit and push
git add .
git commit -m "Add new feature"
git push origin feature/new-feature
```

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Query Documentation](https://tanstack.com/query/latest)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [TypeScript Documentation](https://www.typescriptlang.org/docs)
- [Framer Motion Documentation](https://www.framer.com/motion)

## 📞 Support

For issues and questions:
- Check the troubleshooting section above
- Review browser console for error messages
- Verify backend connectivity and logs
- Submit GitHub issues with detailed reproduction steps

---

## 🎉 Features Delivered

✅ **Modern React/Next.js Frontend** - Full TypeScript application  
✅ **LLM Chat Integration** - Direct medical AI assistant in the UI  
✅ **Database Connectivity** - Real-time data from backend  
✅ **Multi-Modal Triage** - Text, images, and structured data submission  
✅ **Real-Time Dashboard** - Live metrics and system monitoring  
✅ **Responsive Design** - Works on all device sizes  
✅ **Medical Theme** - Custom healthcare-focused UI design  
✅ **File Upload Support** - Drag-and-drop medical image uploads  

The frontend is now ready for production use with full integration to your Medical Triage-BOTS backend! 🏥💻✨