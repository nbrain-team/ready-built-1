#!/usr/bin/env python3
"""
Seed Marketing Calendar with AI-Agency Portal Launch Campaign
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import SessionLocal, User
from core.social_media_models import SocialMediaPost, PostStatus, SocialPlatform
from datetime import datetime, timedelta
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agency-AI Portal Launch Campaign Content
CAMPAIGN_POSTS = [
    # Pre-launch teasers (Early July - Already published)
    {
        "platform": "linkedin",
        "content": "🚀 Big announcement coming soon! We're building something that will revolutionize how agencies leverage AI. Stay tuned... #AI #Innovation #AgencyLife #ComingSoon",
        "scheduled_date": datetime(2025, 7, 1, 10, 0),
        "status": "published",
        "campaign": "Pre-Launch Teaser"
    },
    {
        "platform": "facebook",
        "content": "🤔 What if you could have an AI assistant that understands your agency's unique needs? What if it could handle client communications, generate proposals, and manage tasks? Soon, you won't have to imagine... 🚀",
        "scheduled_date": datetime(2025, 7, 3, 14, 0),
        "status": "published",
        "campaign": "Pre-Launch Teaser"
    },
    {
        "platform": "twitter",
        "content": "Counting down to something BIG! 🎯 AI + Agency Operations = Game Changer. July 15th marks a new era. #AgencyAI #Innovation #LaunchingSoon",
        "scheduled_date": datetime(2025, 7, 5, 12, 0),
        "status": "published",
        "campaign": "Pre-Launch Teaser"
    },
    
    # Launch week content (July 8-14)
    {
        "platform": "linkedin",
        "content": "📧 Email chaos? Not anymore! Our new Agency-AI Portal features intelligent email management that learns your communication style and helps you stay on top of every client conversation. #EmailManagement #AI #Productivity",
        "scheduled_date": datetime(2025, 7, 8, 9, 0),
        "status": "published",
        "campaign": "Feature Highlight"
    },
    {
        "platform": "facebook",
        "content": "✨ FEATURE SPOTLIGHT: Smart Task Management\n\nOur AI doesn't just create tasks - it predicts what needs to be done based on client communications and project patterns. Never miss a deadline again! 🎯\n\nLaunching July 15th!",
        "scheduled_date": datetime(2025, 7, 9, 15, 0),
        "status": "published",
        "campaign": "Feature Highlight"
    },
    {
        "platform": "linkedin",
        "content": "🎉 IT'S OFFICIAL! Introducing the Agency-AI Portal - Your intelligent command center for agency operations.\n\n✅ AI-Powered Client Intelligence\n✅ Smart Email & Calendar Sync\n✅ Automated Task Suggestions\n✅ Real-time Collaboration\n\nJoin the waitlist: command.nbrain.ai\n\n#AgencyAI #LaunchDay #Innovation",
        "scheduled_date": datetime(2025, 7, 10, 10, 0),
        "status": "published",
        "campaign": "Launch Announcement"
    },
    
    # Future scheduled posts (After July 11)
    {
        "platform": "linkedin",
        "content": "🎯 CLIENT SUCCESS STORY: 'We reduced our response time by 60% and increased client satisfaction to 95% using the Agency-AI Portal's intelligent communication features.' - Sarah Chen, Digital Marketing Director\n\nReady to transform your agency? Visit command.nbrain.ai\n\n#ClientSuccess #AgencyAI #Testimonial",
        "scheduled_date": datetime(2025, 7, 12, 11, 0),
        "status": "scheduled",
        "campaign": "Social Proof"
    },
    {
        "platform": "facebook",
        "content": "🚀 LAUNCH WEEK SPECIAL: Sign up for Agency-AI Portal this week and get:\n\n🎁 3 months free premium features\n🎁 1-on-1 onboarding session\n🎁 Custom AI training for your agency\n\nLimited spots available! Register at command.nbrain.ai\n\n#LaunchWeek #SpecialOffer #AgencyAI",
        "scheduled_date": datetime(2025, 7, 13, 14, 0),
        "status": "scheduled",
        "campaign": "Launch Offer"
    },
    {
        "platform": "twitter",
        "content": "🧠 Did you know? Our AI analyzes thousands of agency interactions to provide personalized insights for YOUR specific clients. It's like having a senior strategist working 24/7! #AI #AgencyTech #Innovation",
        "scheduled_date": datetime(2025, 7, 14, 16, 0),
        "status": "scheduled",
        "campaign": "Educational"
    },
    {
        "platform": "linkedin",
        "content": "📊 THE NUMBERS SPEAK:\n\n• 40% reduction in admin time\n• 3x faster proposal generation\n• 95% client satisfaction rate\n• 60% improvement in project delivery\n\nThese aren't projections - they're real results from agencies using Agency-AI Portal.\n\nSee the platform in action: command.nbrain.ai/demo\n\n#ROI #AgencyGrowth #DataDriven",
        "scheduled_date": datetime(2025, 7, 15, 10, 0),
        "status": "scheduled",
        "campaign": "ROI Focus"
    },
    {
        "platform": "facebook",
        "content": "🎥 LIVE DEMO TOMORROW! \n\nJoin our CEO for a live walkthrough of the Agency-AI Portal. See how AI can transform your:\n\n• Client Communications\n• Project Management  \n• Team Collaboration\n• Business Intelligence\n\nRegister: command.nbrain.ai/live-demo\n\nQuestions? Drop them in the comments! 👇",
        "scheduled_date": datetime(2025, 7, 16, 15, 0),
        "status": "scheduled",
        "campaign": "Event Promotion"
    },
    {
        "platform": "linkedin",
        "content": "🤝 PARTNERSHIP ANNOUNCEMENT: We're thrilled to partner with leading agencies worldwide to shape the future of AI-powered agency operations.\n\nSpecial thanks to our beta partners who helped us build something truly revolutionary.\n\nInterested in becoming a partner? Let's connect!\n\n#Partnership #AgencyAI #Collaboration",
        "scheduled_date": datetime(2025, 7, 18, 11, 0),
        "status": "scheduled",
        "campaign": "Partnership"
    },
    {
        "platform": "twitter",
        "content": "⚡ Quick tip: Use our AI's natural language commands to create tasks, schedule meetings, and draft emails - all from one chat interface! 'Schedule a follow-up with Client X next Tuesday' - Done! ✅ #ProductivityHack #AI",
        "scheduled_date": datetime(2025, 7, 19, 13, 0),
        "status": "scheduled",
        "campaign": "Tips & Tricks"
    },
    {
        "platform": "facebook",
        "content": "🎨 Behind the scenes: Our AI doesn't just process data - it understands context, tone, and urgency. Watch how it crafts the perfect client email based on your communication history and current project status.\n\n[Video Demo Link]\n\nTry it yourself: command.nbrain.ai\n\n#BehindTheScenes #AI #Innovation",
        "scheduled_date": datetime(2025, 7, 20, 14, 0),
        "status": "scheduled",
        "campaign": "Product Demo"
    },
    {
        "platform": "linkedin",
        "content": "📈 CASE STUDY: How a boutique creative agency scaled from 5 to 50 clients without adding admin staff.\n\nThe secret? Agency-AI Portal's intelligent automation:\n\n• Automated client onboarding\n• AI-powered communication management\n• Smart task delegation\n• Real-time performance insights\n\nRead the full story: command.nbrain.ai/case-studies\n\n#CaseStudy #AgencyGrowth #Automation",
        "scheduled_date": datetime(2025, 7, 22, 10, 0),
        "status": "scheduled",
        "campaign": "Case Study"
    },
    {
        "platform": "twitter",
        "content": "🏆 Milestone: 100+ agencies now using Agency-AI Portal! Thank you for trusting us to power your growth. Here's to the next 1000! 🥂 #Milestone #ThankYou #AgencyAI",
        "scheduled_date": datetime(2025, 7, 24, 15, 0),
        "status": "scheduled",
        "campaign": "Milestone"
    },
    {
        "platform": "facebook",
        "content": "💡 WEEKLY WEBINAR: 'Mastering AI for Agency Success'\n\nEvery Thursday at 2 PM EST, join us to learn:\n\n• Advanced AI features and shortcuts\n• Best practices from top agencies\n• Q&A with our product team\n• Exclusive tips and strategies\n\nRegister for this week: command.nbrain.ai/webinar\n\n#Webinar #Learning #AgencyAI",
        "scheduled_date": datetime(2025, 7, 25, 11, 0),
        "status": "scheduled",
        "campaign": "Educational"
    },
    {
        "platform": "linkedin",
        "content": "🚀 COMING SOON: Agency-AI Portal 2.0\n\nBased on your feedback, we're already working on:\n\n• Advanced reporting dashboards\n• Multi-language support\n• Custom AI model training\n• White-label options\n\nWhat features would you like to see? Comment below!\n\n#ProductDevelopment #ComingSoon #Innovation",
        "scheduled_date": datetime(2025, 7, 26, 10, 0),
        "status": "scheduled",
        "campaign": "Future Features"
    },
    {
        "platform": "twitter",
        "content": "🎯 Friday productivity tip: Let AI handle the routine so you can focus on the creative. Our users save 8+ hours per week on admin tasks. What would you do with an extra day? #FridayMotivation #Productivity #AI",
        "scheduled_date": datetime(2025, 7, 28, 9, 0),
        "status": "scheduled",
        "campaign": "Engagement"
    },
    {
        "platform": "linkedin",
        "content": "📊 JULY RECAP: One month since launch!\n\n• 500+ agencies onboarded\n• 50,000+ tasks automated\n• 95% user satisfaction\n• 24/7 uptime maintained\n\nThank you for making Agency-AI Portal the fastest-growing agency platform! 🎉\n\nNot yet on board? August special: command.nbrain.ai/august-offer\n\n#MonthlyRecap #Growth #Success",
        "scheduled_date": datetime(2025, 7, 31, 11, 0),
        "status": "scheduled",
        "campaign": "Monthly Recap"
    }
]

# Email campaign posts (these will show as 'email' type in the system)
EMAIL_CAMPAIGNS = [
    {
        "platform": "linkedin",  # Using LinkedIn to represent email campaigns
        "content": "📧 EMAIL CAMPAIGN: Welcome Series - Day 1\nSubject: Welcome to the Future of Agency Management!\nAudience: New signups\nGoal: Onboarding and activation",
        "scheduled_date": datetime(2025, 7, 15, 8, 0),
        "status": "scheduled",
        "campaign": "Email - Welcome Series"
    },
    {
        "platform": "linkedin",  # Using LinkedIn to represent email campaigns
        "content": "📧 EMAIL CAMPAIGN: Feature Spotlight - AI Task Management\nSubject: Never Miss a Deadline Again with AI\nAudience: Active users\nGoal: Feature adoption",
        "scheduled_date": datetime(2025, 7, 17, 8, 0),
        "status": "scheduled",
        "campaign": "Email - Feature Series"
    }
]

# SMS campaign posts
SMS_CAMPAIGNS = [
    {
        "platform": "twitter",  # Using Twitter to represent SMS due to character limits
        "content": "📱 SMS: Your Agency-AI Portal is ready! Login at command.nbrain.ai to start your AI journey. Need help? Reply HELP",
        "scheduled_date": datetime(2025, 7, 15, 12, 0),
        "status": "scheduled",
        "campaign": "SMS - Activation"
    },
    {
        "platform": "twitter",  # Using Twitter to represent SMS
        "content": "📱 SMS: Limited time! Get 3 months free premium features when you upgrade this week. Visit command.nbrain.ai/upgrade",
        "scheduled_date": datetime(2025, 7, 20, 10, 0),
        "status": "scheduled",
        "campaign": "SMS - Promotion"
    }
]

def seed_marketing_calendar():
    """Seed the marketing calendar with Agency-AI Portal launch campaign"""
    
    db = SessionLocal()
    
    try:
        # Get the first user to assign as creator
        user = db.query(User).first()
        if not user:
            logger.error("No users found in database. Please create a user first.")
            return
        
        logger.info(f"Using user {user.email} as content creator")
        
        # Clear existing posts for a fresh campaign
        db.query(SocialMediaPost).delete()
        db.commit()
        logger.info("Cleared existing posts for fresh campaign")
        
        # Add all campaign posts
        all_posts = CAMPAIGN_POSTS + EMAIL_CAMPAIGNS + SMS_CAMPAIGNS
        
        for post_data in all_posts:
            # Determine if post is published (before July 11, 2025)
            if post_data['scheduled_date'] < datetime(2025, 7, 11, 16, 0):
                post_data['status'] = 'published'
                published_date = post_data['scheduled_date'] + timedelta(minutes=5)
            else:
                published_date = None
            
            post = SocialMediaPost(
                platform=SocialPlatform[post_data['platform']],
                content=post_data['content'],
                scheduled_date=post_data['scheduled_date'],
                published_date=published_date,
                status=PostStatus[post_data['status'].upper()],
                created_by=user.id,
                campaign_name=post_data.get('campaign', 'Agency-AI Launch')
            )
            db.add(post)
            logger.info(f"Added {post_data['platform']} post for {post_data['scheduled_date'].strftime('%B %d at %I:%M %p')} - Status: {post_data['status']}")
        
        db.commit()
        logger.info("Successfully seeded marketing calendar with Agency-AI Portal launch campaign!")
        
        # Show summary
        total_posts = db.query(SocialMediaPost).count()
        scheduled = db.query(SocialMediaPost).filter(SocialMediaPost.status == PostStatus.SCHEDULED).count()
        published = db.query(SocialMediaPost).filter(SocialMediaPost.status == PostStatus.PUBLISHED).count()
        
        logger.info(f"\nCampaign Summary:")
        logger.info(f"Total posts: {total_posts}")
        logger.info(f"Published (before July 11): {published}")
        logger.info(f"Scheduled (after July 11): {scheduled}")
        logger.info(f"\nPlatform breakdown:")
        
        for platform in ['linkedin', 'facebook', 'twitter']:
            count = db.query(SocialMediaPost).filter(
                SocialMediaPost.platform == SocialPlatform[platform]
            ).count()
            logger.info(f"{platform.title()}: {count} posts")
        
    except Exception as e:
        logger.error(f"Error seeding marketing calendar: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_marketing_calendar() 