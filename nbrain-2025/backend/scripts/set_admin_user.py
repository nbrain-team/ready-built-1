import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_db, User
from core.auth import get_password_hash
import getpass

def create_or_update_admin():
    """Create a new admin user or update an existing user to admin role."""
    
    db = next(get_db())
    
    try:
        print("\n=== Admin User Setup ===\n")
        
        # Check for existing users
        users = db.query(User).all()
        
        if users:
            print("Existing users:")
            for i, user in enumerate(users):
                print(f"{i+1}. {user.email} (role: {getattr(user, 'role', 'user')})")
            
            choice = input("\nDo you want to (1) create a new admin or (2) make an existing user admin? [1/2]: ").strip()
            
            if choice == "2":
                user_num = int(input("Enter the number of the user to make admin: ")) - 1
                if 0 <= user_num < len(users):
                    user = users[user_num]
                    user.role = "admin"
                    db.commit()
                    print(f"\n✓ Successfully updated {user.email} to admin role!")
                    return
                else:
                    print("Invalid selection.")
                    return
        
        # Create new admin user
        email = input("Enter admin email: ").strip()
        
        # Check if user already exists
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"User {email} already exists. Updating to admin role...")
            existing.role = "admin"
            db.commit()
            print(f"\n✓ Successfully updated {email} to admin role!")
            return
        
        # Get password
        password = getpass.getpass("Enter admin password: ")
        confirm_password = getpass.getpass("Confirm password: ")
        
        if password != confirm_password:
            print("❌ Passwords do not match!")
            return
        
        # Get optional profile info
        first_name = input("First name (optional): ").strip() or None
        last_name = input("Last name (optional): ").strip() or None
        company = input("Company (optional): ").strip() or None
        
        # Create admin user
        admin_user = User(
            email=email,
            hashed_password=get_password_hash(password),
            role="admin",
            is_active=True,
            first_name=first_name,
            last_name=last_name,
            company=company,
            permissions={
                "chat": True,
                "history": True,
                "email-personalizer": True,
                "agent-ideas": True,
                "knowledge": True,
                "crm": True,
                "clients": True,
                "oracle": True,
                "admin": True
            }
        )
        
        db.add(admin_user)
        db.commit()
        
        print(f"\n✓ Successfully created admin user: {email}")
        print("  This user has full access to all modules and admin dashboard.")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_or_update_admin() 