import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useState } from 'react';
import { MessageCircle } from 'lucide-react';

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
        { icon: MessageCircle, label: 'Chat', action: handleNewChatClick, isButton: true, permission: 'chat' },
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
            <div className="sidebar-logo-placeholder">
                <div className="text-2xl font-bold text-blue-600">nB</div>
            </div>
            
            <div className="sidebar-nav-group">
                {visibleNavItems.map((item, index) => {
                    const Icon = item.icon;
                    return (
                        <button key={index} className="sidebar-nav-item" title={item.label} onClick={item.action}>
                            <Icon className="w-6 h-6" />
                            <span className="sidebar-nav-label">{item.label}</span>
                        </button>
                    );
                })}
            </div>
            
            <div style={{ flexGrow: 1 }}></div>
            
            {/* Removed Profile section to keep sidebar minimal */}
        </div>
    );
}; 