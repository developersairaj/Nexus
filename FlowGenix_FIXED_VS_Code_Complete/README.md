# FlowGenix - Advanced Focus Mode App

FlowGenix is a powerful productivity app similar to Forest but with enhanced features including multiple animation themes (K-Pop, Anime, Car, Music), AI chatbot integration, camera monitoring, and app blocking capabilities.

## ✨ Features

### 🔐 Authentication
- **Login/Register** - Secure authentication system
- **Google OAuth** - Quick login with Google account access

### ⏰ Focus Timer
- **Pomodoro Timer** - Customizable focus sessions (5-60 minutes)
- **Theme Animations** - Choose from 4 beautiful themes with unique animations:
  - 🌟 **K-Pop Flow** - Energetic and vibrant
  - ⚡ **Anime Power** - Dynamic and powerful
  - 🏎️ **Racing Mode** - Fast and sleek
  - 🎵 **Music Vibes** - Rhythmic and melodic
- **Progress Tracking** - Visual progress rings and statistics
- **Background Music** - Theme-specific ambient sounds

### 📹 Camera Monitoring
- **Random Focus Checks** - Periodically check if user is studying
- **Privacy Focused** - Camera overlay with user control
- **Smart Notifications** - Gentle reminders to stay focused

### 💰 Reward System
- **Focus Coins** - Earn coins based on focus time (1 coin per 5 minutes)
- **Reward Store** - Redeem coins for treats and breaks
- **Achievement System** - Track milestones and accomplishments

### 📋 Task Management
- **Todo List** - Add, prioritize, and track tasks
- **Due Dates** - Set deadlines with priority levels
- **Progress Tracking** - Visual completion statistics

### 📅 Smart Calendar
- **Event Scheduling** - Add events with time and descriptions
- **Voice Reminders** - Smart timing for notifications:
  - Morning events → Reminded previous night
  - Afternoon events → Reminded in the morning
- **Integration** - Seamlessly connected with focus sessions

### 🤖 AI Chatbot
- **Smart Assistant** - AI-powered productivity companion
- **Focus Guidance** - Tips and motivation for better focus
- **Context Aware** - Understands your progress and goals
- **Quick Actions** - Fast access to common questions

### 🎨 Customization
- **Dynamic Themes** - Complete UI transformation per theme
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Progressive Web App** - Install on any device
- **Dark Mode** - Beautiful glass morphism design

### 🔒 App Blocking (Future Feature)
- **Focus Mode** - Block distracting applications during sessions
- **Whitelist** - Keep essential apps like calls, WhatsApp, camera, email
- **Multi-Device** - Sync across all connected devices
- **Teacher Mode** - Enhanced controls for educational environments

### 📊 Analytics & History
- **Detailed Statistics** - Track focus time, sessions, and progress
- **Visual Charts** - Beautiful progress visualization
- **Achievement Badges** - Earn rewards for consistent focus
- **Export Data** - Download your productivity history

## 🚀 Technology Stack

### Frontend
- **React 18** - Modern React with hooks and context
- **Tailwind CSS** - Utility-first styling with custom themes
- **Framer Motion** - Smooth animations and transitions
- **Progressive Web App** - Native app-like experience
- **Service Workers** - Offline functionality and caching

### Key Libraries
- **React Router** - Client-side routing
- **Lucide React** - Beautiful icon library
- **React Hot Toast** - Elegant notifications
- **Date-fns** - Date manipulation utilities
- **Recharts** - Data visualization (ready for charts)

### PWA Features
- **Offline Support** - Works without internet connection
- **Install Prompt** - Add to home screen on mobile
- **Push Notifications** - Background notifications
- **Background Sync** - Sync data when online

## 📦 Installation & Setup

### Prerequisites
- Node.js 16+ and npm
- Modern web browser with PWA support

### Quick Start

1. **Extract and Navigate**
   ```bash
   # Navigate to the FlowGenix folder
   cd FlowGenix
   ```

2. **Install Dependencies**
   ```bash
   npm install
   ```

3. **Start Development Server**
   ```bash
   npm start
   ```

4. **Access the App**
   - Open http://localhost:3000 in your browser
   - For mobile testing, use your local IP (e.g., http://192.168.1.100:3000)

### Production Build

```bash
# Build for production
npm run build

# Serve the build (requires global serve package)
npx serve -s build
```

## 📱 PWA Installation

### Desktop
1. Open FlowGenix in Chrome/Edge
2. Look for install prompt in address bar
3. Click "Install" to add to desktop

### Mobile
1. Open in mobile browser
2. Tap browser menu
3. Select "Add to Home Screen"
4. FlowGenix will work like a native app

## 🎮 How to Use

### Getting Started
1. **Create Account** - Register or login with Google
2. **Choose Theme** - Select your preferred animation theme
3. **Start Focusing** - Set timer duration and begin your session
4. **Earn Rewards** - Collect coins and redeem for treats
5. **Track Progress** - View your focus history and achievements

### Focus Session Flow
1. **Setup** - Choose duration (5-60 minutes) and theme
2. **Optional Features** - Enable camera monitoring and background music
3. **Focus Time** - Stay focused while the timer counts down
4. **Completion** - Earn coins and view session summary
5. **Rewards** - Use coins in the reward store

### Advanced Features
- **Voice Reminders** - Schedule events with smart notifications
- **AI Assistant** - Chat with the bot for motivation and tips
- **Task Management** - Create and manage your todo list
- **Theme Switching** - Change themes anytime to match your mood

## 🎨 Themes Overview

### 🌟 K-Pop Flow
- **Colors**: Pink, Purple, Teal gradients
- **Vibe**: Energetic and vibrant
- **Best For**: Creative work and high-energy study sessions

### ⚡ Anime Power  
- **Colors**: Red, Blue, Yellow accents
- **Vibe**: Dynamic and powerful
- **Best For**: Challenging tasks and intense focus

### 🏎️ Racing Mode
- **Colors**: Orange, Gray, metallic tones
- **Vibe**: Fast and sleek
- **Best For**: Time-pressured work and competitive studying

### 🎵 Music Vibes
- **Colors**: Purple, Pink, Cyan gradients  
- **Vibe**: Rhythmic and melodic
- **Best For**: Relaxed focus and creative projects

## 🔧 Development Features

### Code Structure
```
src/
├── components/          # React components
│   ├── auth/           # Authentication
│   ├── timer/          # Focus timer
│   ├── todo/           # Task management
│   ├── calendar/       # Event scheduling
│   ├── rewards/        # Reward system
│   ├── chatbot/        # AI assistant
│   ├── history/        # Progress tracking
│   └── themes/         # Theme selection
├── contexts/           # React context providers
├── hooks/              # Custom React hooks
├── services/           # API and external services
└── utils/              # Utility functions
```

### State Management
- **React Context** - Global state management
- **Local Storage** - Persistent data storage
- **Session Storage** - Temporary session data

### Responsive Design
- **Mobile First** - Optimized for mobile devices
- **Tablet Support** - Great experience on tablets
- **Desktop Ready** - Full desktop functionality

## 🚀 Future Enhancements

### Planned Features
- **Real AI Integration** - OpenAI/Gemini API for smarter chatbot
- **Advanced Analytics** - Detailed productivity insights
- **Social Features** - Study groups and leaderboards
- **App Blocking** - Native app blocking on desktop
- **Teacher Dashboard** - Classroom management features
- **Data Export** - CSV/JSON export capabilities
- **Custom Themes** - User-created theme system

### Technical Improvements
- **Real-time Sync** - Cloud synchronization
- **Offline First** - Enhanced offline capabilities
- **Performance** - Lazy loading and code splitting
- **Accessibility** - Full WCAG compliance
- **Testing** - Comprehensive test coverage

## 🤝 Contributing

FlowGenix is built with modern web technologies and follows best practices. The codebase is well-structured and documented for easy contribution.

### Development Guidelines
- Use functional components with hooks
- Follow the existing theme system
- Maintain responsive design principles
- Write clean, documented code
- Test on multiple devices and browsers

## 📄 License

This project is created for educational and productivity purposes. All rights reserved.

## 🙏 Acknowledgments

- Inspired by the Forest app concept
- Built with love for the productivity community
- Special thanks to all the amazing open-source libraries used

---

**Start your focus journey with FlowGenix today! 🚀✨**
