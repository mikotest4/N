import motor.asyncio
from config import DATABASE_URL, DATABASE_NAME
from datetime import datetime, timedelta
from pytz import timezone

# MongoDB connection
client = motor.asyncio.AsyncIOMotorClient(DATABASE_URL)
db = client[DATABASE_NAME]
collection = db["premium_users"]

# Function to add premium user to database
async def add_premium_user_to_db(user_id, days):
    """
    Add premium user to database with expiration date
    Args:
        user_id: Telegram user ID
        days: Number of days for premium (or 'test' for 1 minute)
    Returns:
        Tuple: (success: bool, expiration_time: datetime)
    """
    try:
        # Calculate expiration date
        ist = timezone("Asia/Kolkata")
        current_time = datetime.now(ist)
        
        # Handle test plan (1 minute)
        if days == "test":
            expiration_time = current_time + timedelta(minutes=1)
        else:
            expiration_time = current_time + timedelta(days=int(days))
        
        # Format expiration timestamp
        expiration_timestamp = expiration_time.isoformat()
        
        # Check if user already exists in premium collection
        existing_user = await collection.find_one({"user_id": user_id})
        
        if existing_user:
            # Update existing user's expiration time
            await collection.update_one(
                {"user_id": user_id},
                {"$set": {"expiration_timestamp": expiration_timestamp}}
            )
            print(f"Updated premium for user {user_id} until {expiration_time}")
        else:
            # Add new premium user
            await collection.insert_one({
                "user_id": user_id,
                "expiration_timestamp": expiration_timestamp
            })
            print(f"Added new premium user {user_id} until {expiration_time}")
        
        return True, expiration_time
    except Exception as e:
        print(f"Error adding premium user to DB: {e}")
        return False, None

# Function to check if user is premium
async def is_premium_user(user_id):
    """
    Check if user has active premium membership
    Args:
        user_id: Telegram user ID
    Returns:
        bool: True if user is premium, False otherwise
    """
    try:
        user = await collection.find_one({"user_id": user_id})
        if not user:
            return False
            
        # Check if premium has expired
        ist = timezone("Asia/Kolkata")
        current_time = datetime.now(ist)
        expiration_time = datetime.fromisoformat(user["expiration_timestamp"])
        
        if current_time > expiration_time:
            # Remove expired premium user
            await collection.delete_one({"user_id": user_id})
            print(f"Removed expired premium user {user_id}")
            return False
            
        return True
    except Exception as e:
        print(f"Error checking premium user: {e}")
        return False

# Function to get premium expiration date
async def get_premium_expiration(user_id):
    """
    Get premium expiration date for user
    Args:
        user_id: Telegram user ID
    Returns:
        datetime: Expiration date or None if not premium
    """
    try:
        user = await collection.find_one({"user_id": user_id})
        if not user:
            return None
            
        return datetime.fromisoformat(user["expiration_timestamp"])
    except Exception as e:
        print(f"Error getting premium expiration: {e}")
        return None

# Function to remove premium user
async def remove_premium_user(user_id):
    """
    Remove premium user from database
    Args:
        user_id: Telegram user ID
    Returns:
        bool: True if removed successfully, False otherwise
    """
    try:
        result = await collection.delete_one({"user_id": user_id})
        if result.deleted_count > 0:
            print(f"Removed premium user {user_id}")
            return True
        else:
            print(f"Premium user {user_id} not found")
            return False
    except Exception as e:
        print(f"Error removing premium user: {e}")
        return False

# Function to get all premium users
async def get_all_premium_users():
    """
    Get all premium users from database
    Returns:
        list: List of premium user documents
    """
    try:
        users = []
        async for user in collection.find({}):
            users.append(user)
        return users
    except Exception as e:
        print(f"Error getting all premium users: {e}")
        return []

# Function to clean expired premium users
async def clean_expired_premium_users():
    """
    Remove all expired premium users from database
    Returns:
        int: Number of users removed
    """
    try:
        ist = timezone("Asia/Kolkata")
        current_time = datetime.now(ist)
        
        # Find expired users
        expired_users = []
        async for user in collection.find({}):
            expiration_time = datetime.fromisoformat(user["expiration_timestamp"])
            if current_time > expiration_time:
                expired_users.append(user["user_id"])
        
        # Remove expired users
        if expired_users:
            await collection.delete_many({"user_id": {"$in": expired_users}})
            print(f"Cleaned {len(expired_users)} expired premium users")
            
        return len(expired_users)
    except Exception as e:
        print(f"Error cleaning expired premium users: {e}")
        return 0

# Function to extend premium membership
async def extend_premium_membership(user_id, additional_days):
    """
    Extend existing premium membership
    Args:
        user_id: Telegram user ID
        additional_days: Additional days to add
    Returns:
        Tuple: (success: bool, new_expiration_time: datetime)
    """
    try:
        user = await collection.find_one({"user_id": user_id})
        if not user:
            return False, None
            
        # Get current expiration time
        current_expiration = datetime.fromisoformat(user["expiration_timestamp"])
        
        # Calculate new expiration time
        ist = timezone("Asia/Kolkata")
        current_time = datetime.now(ist)
        
        # If current premium is still valid, extend from expiration date
        # If expired, extend from current time
        if current_expiration > current_time:
            new_expiration = current_expiration + timedelta(days=additional_days)
        else:
            new_expiration = current_time + timedelta(days=additional_days)
        
        # Update database
        await collection.update_one(
            {"user_id": user_id},
            {"$set": {"expiration_timestamp": new_expiration.isoformat()}}
        )
        
        print(f"Extended premium for user {user_id} until {new_expiration}")
        return True, new_expiration
    except Exception as e:
        print(f"Error extending premium membership: {e}")
        return False, None

# Function to get premium stats
async def get_premium_stats():
    """
    Get premium membership statistics
    Returns:
        dict: Statistics about premium users
    """
    try:
        total_users = await collection.count_documents({})
        
        # Count active vs expired users
        ist = timezone("Asia/Kolkata")
        current_time = datetime.now(ist)
        
        active_users = 0
        expired_users = 0
        
        async for user in collection.find({}):
            expiration_time = datetime.fromisoformat(user["expiration_timestamp"])
            if current_time > expiration_time:
                expired_users += 1
            else:
                active_users += 1
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "expired_users": expired_users
        }
    except Exception as e:
        print(f"Error getting premium stats: {e}")
        return {
            "total_users": 0,
            "active_users": 0,
            "expired_users": 0
        }

# Function to get premium user info
async def get_premium_user_info(user_id):
    """
    Get detailed information about a premium user
    Args:
        user_id: Telegram user ID
    Returns:
        dict: User premium information or None
    """
    try:
        user = await collection.find_one({"user_id": user_id})
        if not user:
            return None
            
        expiration_time = datetime.fromisoformat(user["expiration_timestamp"])
        ist = timezone("Asia/Kolkata")
        current_time = datetime.now(ist)
        
        is_active = current_time < expiration_time
        time_remaining = expiration_time - current_time if is_active else timedelta(0)
        
        return {
            "user_id": user_id,
            "expiration_time": expiration_time,
            "is_active": is_active,
            "time_remaining": time_remaining,
            "days_remaining": time_remaining.days if is_active else 0,
            "hours_remaining": time_remaining.seconds // 3600 if is_active else 0
        }
    except Exception as e:
        print(f"Error getting premium user info: {e}")
        return None

# Initialize database indexes for better performance
async def init_premium_db():
    """
    Initialize premium database with proper indexes
    """
    try:
        # Create index on user_id for faster queries
        await collection.create_index("user_id", unique=True)
        
        # Create index on expiration_timestamp for cleanup operations
        await collection.create_index("expiration_timestamp")
        
        print("Premium database initialized successfully")
    except Exception as e:
        print(f"Error initializing premium database: {e}")
