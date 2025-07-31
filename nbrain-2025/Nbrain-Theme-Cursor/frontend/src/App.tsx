import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage';
import KnowledgeBase from './pages/KnowledgeBase';
import HistoryPage from './pages/HistoryPage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import { MainLayout } from './components/MainLayout';
import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import LandingPage from './pages/LandingPage';
import StartPage from './pages/StartPage';
import AgentsPage from './pages/AgentsPage';
import Agents from './pages/Agents';
import CRMPage from './pages/CRMPage';
import VoiceIdeatorPage from './pages/VoiceIdeatorPage';
import { AuthLayout } from './components/AuthLayout';
import { GeneratorWorkflow } from './components/GeneratorWorkflow';
import OraclePage from './pages/OraclePage';
import OracleAuthCallback from './pages/OracleAuthCallback';
import ClientPortal from './pages/ClientPortal';
import ClientDetail from './pages/ClientDetail';
import NewClient from './pages/NewClient';
import { ProfilePage } from './pages/ProfilePage';
import { ProtectedRoute } from './components/ProtectedRoute';
import SocialMediaCalendar from './pages/SocialMediaCalendar';

// Define the structure for a message
interface Message {
  text: string;
  sender: 'user' | 'ai';
  sources?: (string | { source: string })[];
}

// A wrapper for routes that require authentication - using the new component
const AuthenticatedRoute = ({ children }: { children: React.ReactNode }) => {
  return <ProtectedRoute requireAuth={true}>{children}</ProtectedRoute>;
};

function App() {
  return (
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
  );
}

function AppRoutes() {
  const [messages, setMessages] = useState<Message[]>([]);
  const { isAuthenticated } = useAuth();
  // Forcing a new build with a dummy comment
  useEffect(() => {
    setMessages([]);
  }, [isAuthenticated]);

  return (
    <Router>
      <Routes>
        {/* Auth routes with dark theme */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
        </Route>

        {/* OAuth callback route - no protection needed as it handles auth */}
        <Route path="/oracle/auth/callback" element={<OracleAuthCallback />} />

        {/* Protected routes with light theme and sidebar */}
        <Route
          path="/start"
          element={
            <AuthenticatedRoute>
              <StartPage />
            </AuthenticatedRoute>
          }
        />
        <Route
          path="/*"
          element={
            <AuthenticatedRoute>
              <MainLayout onNewChat={() => setMessages([])}>
                <Routes>
                  <Route path="/" element={<HomePage messages={messages} setMessages={setMessages} />} />
                  <Route path="/home" element={<LandingPage />} />
                  <Route path="/knowledge" element={<KnowledgeBase />} />
                  <Route path="/agents" element={<AgentsPage />} />
                  <Route path="/email-personalizer" element={<GeneratorWorkflow />} />
                  <Route path="/agent-ideas" element={<Agents />} />
                  <Route path="/history" element={<HistoryPage />} />
                  <Route path="/crm" element={<CRMPage />} />
                  <Route path="/voice-ideator" element={<VoiceIdeatorPage />} />
                  <Route path="/oracle" element={<OraclePage />} />
                  <Route path="/clients" element={<ClientPortal />} />
                  <Route path="/client/new" element={<NewClient />} />
                  <Route path="/client/:clientId" element={<ClientDetail />} />
                  <Route path="/profile" element={<ProfilePage />} />
                  <Route path="/social-calendar" element={<SocialMediaCalendar />} />
                  <Route path="*" element={<Navigate to="/" />} />
                </Routes>
              </MainLayout>
            </AuthenticatedRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App; 