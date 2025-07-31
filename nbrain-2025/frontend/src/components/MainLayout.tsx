import { Theme } from "@radix-ui/themes";
import { Sidebar } from "./Sidebar";
import React, { useEffect, useState } from "react";
import SuperAgent from "./SuperAgent";
import { useLocation } from "react-router-dom";

interface MainLayoutProps {
    children: React.ReactNode;
    onNewChat: () => void;
}

export const MainLayout = ({ children, onNewChat }: MainLayoutProps) => {
    const [isReady, setIsReady] = useState(false);
    const location = useLocation();
    
    useEffect(() => {
        // Ensure layout is ready before rendering
        setIsReady(true);
    }, []);
    
    if (!isReady) {
        return null; // Prevent flash of unstyled content
    }
    
    // Hide SuperAgent on chat page (root path)
    const showSuperAgent = location.pathname !== '/';
    
    return (
        <>
            <Sidebar onNewChat={onNewChat} />
            <div className="content-area">
                <Theme appearance="light" className="radix-theme-wrapper">
                    {children}
                </Theme>
            </div>
            {showSuperAgent && <SuperAgent />}
        </>
    );
}; 