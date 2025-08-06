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

    // Only keep the Chat item
    const navItems = [
        { icon: '13.png', label: 'Chat', action: handleNewChatClick, isButton: true, permission: 'chat' },
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
                    <button key={index} className="sidebar-nav-item" title={item.label} onClick={item.action}>
                        <img src={`/new-icons/${item.icon}`} alt={item.label} />
                        <span className="sidebar-nav-label">{item.label}</span>
                    </button>
                ))}
            </div>
            
            <div style={{ flexGrow: 1 }}></div>
            
            {/* Removed Profile section to keep sidebar minimal */}
        </div>
    );
}; 