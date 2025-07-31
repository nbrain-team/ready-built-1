import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useState } from 'react';

export const Sidebar = ({ onNewChat }: { onNewChat: () => void }) => {
    const { hasPermission } = useAuth();
    const navigate = useNavigate();
    const [isExpanded, setIsExpanded] = useState(false);

    const handleNewChatClick = () => {
        navigate('/');
        onNewChat();
    };

    const navItems = [
        { icon: '13.png', label: 'Chat', action: handleNewChatClick, isButton: true, permission: 'chat' },
        { icon: '2.png', label: 'History', path: '/history', permission: 'history' },
        { icon: '3.png', label: 'Personalizer', path: '/email-personalizer', permission: 'email-personalizer' },
        { icon: '7.png', label: 'AI Ideator', path: '/agent-ideas', permission: 'agent-ideas' },
        { icon: '4.png', label: 'Documents', path: '/knowledge', permission: 'knowledge' },
        { icon: '14.png', label: 'CRM', path: '/crm', permission: 'crm' },
        { icon: '11.png', label: 'Tasks', path: '/clients', permission: 'clients' },
        { icon: '15.png', label: 'Your Oracle', path: '/oracle', permission: 'oracle' },
        { icon: '8.png', label: 'Marketing Calendar', path: '/social-calendar', permission: 'social-calendar' },
    ];

    // Filter nav items based on permissions
    const visibleNavItems = navItems.filter(item => 
        !item.permission || hasPermission(item.permission)
    );

    return (
        <div 
            className={`sidebar-placeholder ${isExpanded ? 'expanded' : 'collapsed'}`}
            onMouseEnter={() => setIsExpanded(true)}
            onMouseLeave={() => setIsExpanded(false)}
        >
            <Link to="/start" className="sidebar-logo-placeholder">
                <img src="/new-icons/1.png" alt="nBrain Logo" className="sidebar-logo-img" />
            </Link>
            
            <div className="sidebar-nav-group">
                {visibleNavItems.map((item, index) => (
                    item.isButton ? (
                        <button key={index} className="sidebar-nav-item" title={item.label} onClick={item.action}>
                            <img src={`/new-icons/${item.icon}`} alt={item.label} />
                            <span className="sidebar-nav-label">{item.label}</span>
                        </button>
                    ) : (
                        <Link key={index} to={item.path!} className="sidebar-nav-item" title={item.label}>
                            <img src={`/new-icons/${item.icon}`} alt={item.label} />
                            <span className="sidebar-nav-label">{item.label}</span>
                        </Link>
                    )
                ))}
            </div>
            
            <div style={{ flexGrow: 1 }}></div>
            
            <div className="sidebar-nav-group">
                <Link to="/profile" className="sidebar-nav-item" title="Profile">
                    <img src="/new-icons/6.png" alt="Profile" />
                    <span className="sidebar-nav-label">Profile</span>
                </Link>
            </div>
        </div>
    );
}; 